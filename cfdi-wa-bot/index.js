const { Client, LocalAuth, MessageMedia } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const axios = require("axios");
const { existsSync, readFileSync } = require("node:fs");
const { writeFile } = require("node:fs/promises");
const { resolve } = require("node:path");

loadEnvFile();

const API_BASE = process.env.CFDI_API_BASE || "http://127.0.0.1:8000/api/v1";
const API_TOKEN = process.env.CFDI_API_TOKEN || "";
const API_EMAIL = (process.env.CFDI_API_EMAIL || "").trim();
const API_PASSWORD = process.env.CFDI_API_PASSWORD || "";
const API_AUTH_SKEW_MS = Number(process.env.CFDI_API_AUTH_SKEW_MS || 120000);
const API_TIMEOUT_MS = Number(process.env.CFDI_API_TIMEOUT_MS || 15000);
const COMMAND_COOLDOWN_MS = Number(process.env.WA_COMMAND_COOLDOWN_MS || 2500);
const STATUS_FILE = process.env.WA_STATUS_FILE || "bot-status.json";
const READY_TIMEOUT_MS = Number(process.env.WA_READY_TIMEOUT_MS || 90000);
const ALLOW_FROM_ME_COMMANDS =
  String(process.env.WA_ALLOW_FROM_ME_COMMANDS || "true").toLowerCase() === "true";

const api = axios.create({ baseURL: API_BASE, timeout: API_TIMEOUT_MS });
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!axios.isAxiosError(error)) {
      throw error;
    }
    const status = error.response?.status;
    const originalConfig = error.config || {};
    if (originalConfig.skipAuthRetry) {
      throw error;
    }
    if (status !== 401 || originalConfig._retry || !supportsCredentialAuth()) {
      throw error;
    }
    originalConfig._retry = true;
    await ensureAccessToken(true);
    originalConfig.headers = {
      ...(originalConfig.headers || {}),
      Authorization: `Bearer ${accessToken}`,
    };
    return api.request(originalConfig);
  }
);

const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: { headless: true },
  markSeen: false,
});

const lastCommandAt = new Map();
const processedMessageIds = new Map();
let accessToken = API_TOKEN;
let refreshToken = (process.env.CFDI_API_REFRESH_TOKEN || "").trim();
let accessTokenExpiresAt = 0;
let authPromise = null;
let hasLoggedAuthenticated = false;
let hasLoggedReady = false;
let lastTransientLogAt = 0;
let readyTimer = null;
let isRestarting = false;

process.on("unhandledRejection", (err) => {
  if (isTransientNavigationError(err)) {
    const now = Date.now();
    if (now - lastTransientLogAt > 10000) {
      lastTransientLogAt = now;
      console.warn("[WA] Error transitorio de navegacion detectado; se ignora.");
    }
    return;
  }
  console.error("UnhandledRejection:", err);
});

process.on("uncaughtException", (err) => {
  console.error("UncaughtException:", err);
});

client.on("qr", async (qr) => {
  qrcode.generate(qr, { small: true });
  await setBotStatus("waiting_qr", { linked: false, ready: false });
  armReadyWatchdog();
});

client.on("authenticated", async () => {
  if (!hasLoggedAuthenticated) {
    console.log("[WA] Vinculado con exito.");
    hasLoggedAuthenticated = true;
  }
  await setBotStatus("authenticated", { linked: true, ready: false });
  armReadyWatchdog();
});

client.on("auth_failure", async (message) => {
  console.error("[WA] Fallo de autenticacion:", message);
  await setBotStatus("auth_failure", { linked: false, ready: false, message });
});

client.on("loading_screen", async (percent, message) => {
  await setBotStatus("loading", { linked: true, ready: false, percent, message });
});

client.on("change_state", async (state) => {
  await setBotStatus("state_change", { linked: true, ready: false, state });
});

client.on("disconnected", async (reason) => {
  console.warn("[WA] Desconectado:", reason);
  hasLoggedAuthenticated = false;
  hasLoggedReady = false;
  await setBotStatus("disconnected", { linked: false, ready: false, reason });
});

client.on("ready", async () => {
  if (!hasLoggedReady) {
    console.log("[WA] Bot listo para recibir mensajes.");
    console.log("[WA] SIGNAL: BOT_READY");
    hasLoggedReady = true;
  }
  clearReadyWatchdog();
  await setBotStatus("ready", { linked: true, ready: true });
});

client.on("message", handleCommandMessage);
client.on("message_create", handleCommandMessage);

setBotStatus("starting", { linked: false, ready: false }).finally(async () => {
  await bootstrapApiAuth();
  armReadyWatchdog();
  client.initialize();
});

async function handleCommandMessage(msg) {
  const messageId = msg?.id?._serialized;
  if (messageId) {
    const now = Date.now();
    cleanupProcessedIds(now);
    const seenAt = processedMessageIds.get(messageId);
    if (seenAt && now - seenAt < 60_000) {
      return;
    }
    processedMessageIds.set(messageId, now);
  }

  if (!msg || typeof msg.body !== "string") {
    return;
  }
  if (!ALLOW_FROM_ME_COMMANDS && msg.fromMe) {
    return;
  }
  if (msg.from === "status@broadcast") {
    return;
  }

  const text = msg.body.trim();
  if (!text.startsWith("/")) {
    return;
  }

  const [cmd, ...args] = text.split(/\s+/);
  const senderKey = (await resolveSenderPhone(msg)) || String(msg.from || "");
  const cooldownLeft = getCooldownRemainingMs(senderKey);
  if (cooldownLeft > 0) {
    const seconds = Math.ceil(cooldownLeft / 1000);
    await safeReply(msg, `Espera ${seconds}s antes de enviar otro comando.`);
    return;
  }
  markCommandUsage(senderKey);

  try {
    switch (cmd) {
      case "/help":
        await safeReply(msg, helpText());
        break;
      case "/facturas":
        await handleFacturas(msg, args);
        break;
      case "/retenciones":
        await handleRetenciones(msg, args);
        break;
      case "/declaraciones":
        await handleDeclaraciones(msg, args);
        break;
      case "/factura":
        await handleFacturaDetail(msg, args);
        break;
      case "/factura_xml":
        await handleFacturaXml(msg, args);
        break;
      case "/declaracion_pdf":
        await handleDeclaracionPdf(msg, args);
        break;
      case "/retencion":
        await handleRetencionDetail(msg, args);
        break;
      case "/declaracion_resumen":
        await handleDeclaracionResumen(msg, args);
        break;
      case "/summary":
        await handleSummary(msg, args);
        break;
      case "/summary_details":
        await handleSummaryDetails(msg, args);
        break;
      case "/declaracion":
        await handleDeclaracionMode(msg, args);
        break;
      case "/hoja_sat":
        await handleHojaSat(msg, args);
        break;
      case "/sat_csv":
        await handleSatCsv(msg, args);
        break;
      default:
        await safeReply(msg, "Comando no reconocido. Usa /help.");
        break;
    }
  } catch (err) {
    const phone = await resolveSenderPhone(msg);
    console.error("CommandError:", { cmd, from: msg.from, phone, err: formatError(err) });
    await safeReply(msg, toUserErrorMessage(err));
  }
}

function helpText() {
  return [
    "Comandos disponibles:",
    "/facturas <year> <month> [tipo] [naturaleza]",
    "/retenciones <year> <month>",
    "/declaraciones <year> <month>",
    "/factura <factura_id>",
    "/factura_xml <factura_id>",
    "/declaracion_pdf <dec_id> <filename>",
    "/retencion <retencion_id>",
    "/declaracion_resumen <dec_id>",
    "/summary <year> <month>",
    "/summary_details <year> <month>",
    "/declaracion <year> <month> [income_source]",
    "/hoja_sat <year> <month> [income_source]",
    "/sat_csv <year> <month> [income_source]",
  ].join("\n");
}

async function handleFacturas(msg, args) {
  const [yearRaw, monthRaw, tipo, naturaleza] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /facturas <year> <month> [tipo] [naturaleza]");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/facturas", {
    params: { year, month, tipo, naturaleza },
    headers: await buildHeaders(rfc),
  });
  const items = res.data || [];
  if (!items.length) {
    await safeReply(msg, "Sin facturas para ese periodo.");
    return;
  }
  const lines = items.slice(0, 5).map((f) => {
    const total = f.total || f.total_mxn || "";
    return `- ${f.uuid} | ${total} | ${f.emisor_rfc || ""}`;
  });
  await safeReply(msg, `Facturas (${items.length}):\n${lines.join("\n")}`);
}

async function handleRetenciones(msg, args) {
  const [yearRaw, monthRaw] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /retenciones <year> <month>");
    return;
  }

  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/retenciones", {
    params: { year, month },
    headers: await buildHeaders(rfc),
  });
  const items = res.data || [];
  if (!items.length) {
    await safeReply(msg, "Sin retenciones para ese periodo.");
    return;
  }
  const lines = items.slice(0, 5).map((r) => `- ${r.uuid || r.id} | ${r.emisor_rfc || ""} -> ${r.receptor_rfc || ""}`);
  await safeReply(msg, `Retenciones (${items.length}):\n${lines.join("\n")}`);
}

async function handleDeclaraciones(msg, args) {
  const [yearRaw, monthRaw] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /declaraciones <year> <month>");
    return;
  }

  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/declaraciones", {
    params: { year, month },
    headers: await buildHeaders(rfc),
  });
  const items = res.data || [];
  if (!items.length) {
    await safeReply(msg, "Sin declaraciones para ese periodo.");
    return;
  }
  const lines = items.slice(0, 5).map((d) => `- id:${d.id} | ${d.rfc || ""} | ${d.folio || ""}`);
  await safeReply(msg, `Declaraciones (${items.length}):\n${lines.join("\n")}`);
}

async function handleFacturaDetail(msg, args) {
  const facturaId = parsePositiveInt(args[0]);
  if (facturaId === null) {
    await safeReply(msg, "Uso: /factura <factura_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get(`/facturas/${facturaId}`, { headers: await buildHeaders(rfc) });
  await safeReply(msg, `Factura ${facturaId}:\n${formatObject(res.data)}`);
}

async function handleFacturaXml(msg, args) {
  const facturaId = parsePositiveInt(args[0]);
  if (facturaId === null) {
    await safeReply(msg, "Uso: /factura_xml <factura_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get(`/facturas/${facturaId}/xml`, { headers: await buildHeaders(rfc) });
  const text = String(res.data || "");
  const preview = text.length > 3500 ? `${text.slice(0, 3500)}\n...[truncado]` : text;
  await safeReply(msg, preview || "XML vacio.");
}

async function handleDeclaracionPdf(msg, args) {
  const decId = parsePositiveInt(args[0]);
  const filename = String(args[1] || "").trim();
  if (decId === null || !filename) {
    await safeReply(msg, "Uso: /declaracion_pdf <dec_id> <filename>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get(`/declaraciones/${decId}/archivo/${filename}`, {
    responseType: "arraybuffer",
    headers: await buildHeaders(rfc),
  });
  const media = new MessageMedia("application/pdf", Buffer.from(res.data).toString("base64"), filename);
  await msg.reply(media, undefined, { sendMediaAsDocument: true });
}

async function handleRetencionDetail(msg, args) {
  const retencionId = parsePositiveInt(args[0]);
  if (retencionId === null) {
    await safeReply(msg, "Uso: /retencion <retencion_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get(`/retenciones/${retencionId}`, { headers: await buildHeaders(rfc) });
  await safeReply(msg, `Retencion ${retencionId}:\n${formatObject(res.data)}`);
}

async function handleDeclaracionResumen(msg, args) {
  const decId = parsePositiveInt(args[0]);
  if (decId === null) {
    await safeReply(msg, "Uso: /declaracion_resumen <dec_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get(`/declaraciones/${decId}/resumen.json`, { headers: await buildHeaders(rfc) });
  await safeReply(msg, `Resumen declaracion ${decId}:\n${formatObject(res.data)}`);
}

async function handleSummary(msg, args) {
  const [yearRaw, monthRaw] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /summary <year> <month>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/summary", { params: { year, month }, headers: await buildHeaders(rfc) });
  await safeReply(msg, formatSummary(res.data));
}

async function handleSummaryDetails(msg, args) {
  const [yearRaw, monthRaw] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /summary_details <year> <month>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/summary/details", { params: { year, month }, headers: await buildHeaders(rfc) });
  await safeReply(msg, formatSummaryDetails(res.data));
}

async function handleDeclaracionMode(msg, args) {
  const [yearRaw, monthRaw, incomeSource] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /declaracion <year> <month> [income_source]");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/declaracion", {
    params: { year, month, income_source: incomeSource || "auto" },
    headers: await buildHeaders(rfc),
  });
  await safeReply(msg, formatDeclaracionMode(res.data));
}

async function handleHojaSat(msg, args) {
  const [yearRaw, monthRaw, incomeSource] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /hoja_sat <year> <month> [income_source]");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/sat_hoja.txt", {
    params: { year, month, income_source: incomeSource || "auto" },
    headers: await buildHeaders(rfc),
  });
  await safeReply(msg, String(res.data || "Sin respuesta."));
}

async function handleSatCsv(msg, args) {
  const [yearRaw, monthRaw, incomeSource] = args;
  const year = parseYear(yearRaw);
  const month = parseMonth(monthRaw);
  if (year === null || month === null) {
    await safeReply(msg, "Uso: /sat_csv <year> <month> [income_source]");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) return;

  const res = await api.get("/sat_report.csv", {
    params: { year, month, income_source: incomeSource || "auto" },
    headers: await buildHeaders(rfc),
  });
  const lines = String(res.data || "").split("\n").slice(0, 6).join("\n");
  await safeReply(msg, `CSV (primeras lineas):\n${lines}`);
}

function normalizePhone(value) {
  return String(value || "").replace(/\D+/g, "");
}

function parsePositiveInt(value) {
  const n = Number(value);
  return Number.isInteger(n) && n > 0 ? n : null;
}

function parseYear(value) {
  const n = Number(value);
  return Number.isInteger(n) && n >= 2000 && n <= 2100 ? n : null;
}

function parseMonth(value) {
  const n = Number(value);
  return Number.isInteger(n) && n >= 1 && n <= 12 ? n : null;
}

function getCooldownRemainingMs(senderKey) {
  if (!senderKey) return 0;
  const last = lastCommandAt.get(senderKey);
  if (!last) return 0;
  const elapsed = Date.now() - last;
  return elapsed >= COMMAND_COOLDOWN_MS ? 0 : COMMAND_COOLDOWN_MS - elapsed;
}

function markCommandUsage(senderKey) {
  if (senderKey) lastCommandAt.set(senderKey, Date.now());
}

function cleanupProcessedIds(now = Date.now()) {
  for (const [id, ts] of processedMessageIds.entries()) {
    if (now - ts > 120_000) {
      processedMessageIds.delete(id);
    }
  }
}

function supportsCredentialAuth() {
  return Boolean(API_EMAIL && API_PASSWORD);
}

async function bootstrapApiAuth() {
  if (accessToken && !supportsCredentialAuth()) {
    return;
  }
  if (!supportsCredentialAuth()) {
    console.warn("[WA] Sin CFDI_API_TOKEN ni CFDI_API_EMAIL/CFDI_API_PASSWORD. Si la API exige auth, habra respuestas 401.");
    return;
  }
  try {
    await ensureAccessToken(false);
    console.log("[WA] Token API inicializado con login/refresh.");
  } catch (err) {
    console.warn("[WA] No fue posible inicializar auth API al arrancar:", formatError(err));
  }
}

async function loginApi() {
  if (!supportsCredentialAuth()) {
    throw new Error("CFDI_API_EMAIL/CFDI_API_PASSWORD no configurados");
  }
  const res = await api.post("/auth/login", { email: API_EMAIL, password: API_PASSWORD }, { skipAuthRetry: true });
  applyAuthPayload(res.data);
}

async function refreshApi() {
  if (!refreshToken) {
    throw new Error("Refresh token no disponible");
  }
  const res = await api.post("/auth/refresh", { refresh_token: refreshToken }, { skipAuthRetry: true });
  applyAuthPayload(res.data);
}

function applyAuthPayload(payload) {
  accessToken = String(payload?.access_token || "").trim();
  refreshToken = String(payload?.refresh_token || "").trim() || refreshToken;
  const expiresIn = Number(payload?.expires_in || 0);
  accessTokenExpiresAt = expiresIn > 0 ? Date.now() + expiresIn * 1000 : 0;
}

function hasUsableAccessToken() {
  if (!accessToken) return false;
  if (!accessTokenExpiresAt) return true;
  return Date.now() + API_AUTH_SKEW_MS < accessTokenExpiresAt;
}

async function ensureAccessToken(force = false) {
  if (!force && hasUsableAccessToken()) {
    return accessToken;
  }
  if (authPromise) {
    await authPromise;
    return accessToken;
  }
  authPromise = (async () => {
    if (!force && refreshToken) {
      try {
        await refreshApi();
        return;
      } catch {
        // Si refresh falla intentamos login normal.
      }
    }
    if (!force && accessToken && !supportsCredentialAuth()) {
      return;
    }
    await loginApi();
  })();
  try {
    await authPromise;
  } finally {
    authPromise = null;
  }
  return accessToken;
}

async function getAuthHeaders() {
  if (supportsCredentialAuth()) {
    await ensureAccessToken(false);
  }
  const headers = {};
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  return headers;
}

async function buildHeaders(rfc) {
  const headers = await getAuthHeaders();
  headers["X-RFC"] = String(rfc || "").trim().toUpperCase();
  return headers;
}

async function resolveSenderPhone(msg) {
  try {
    const contact = await msg.getContact();
    const byContact = normalizePhone(contact?.number || contact?.id?.user || contact?.id?._serialized);
    if (byContact) {
      return byContact;
    }
  } catch (err) {
    // Fallback silencioso a null para que el caller maneje respuesta al usuario.
  }
  return null;
}

async function requireRfc(msg) {
  const phone = await resolveSenderPhone(msg);
  if (!phone) {
    await safeReply(msg, "No pude identificar tu telefono para resolver el RFC.");
    return null;
  }
  try {
    const res = await api.get("/rfc-phones/resolve", {
      params: { phone },
      headers: await getAuthHeaders(),
    });
    const rfc = res.data?.rfc;
    if (!rfc) {
      await safeReply(msg, "No hay RFC asociado a tu telefono. Pide al admin que lo registre.");
      return null;
    }
    return rfc;
  } catch (err) {
    if (err?.response?.status === 404) {
      await safeReply(msg, "Telefono no registrado. Pide al admin que lo registre con tu RFC.");
      return null;
    }
    throw err;
  }
}

function toUserErrorMessage(err) {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status;
    if (status === 400) return "Solicitud invalida. Revisa el formato del comando.";
    if (status === 401 || status === 403) return "No tienes permisos para esta operacion.";
    if (status === 404) return "No se encontro la informacion solicitada.";
    if (status === 408 || status === 504) return "La API tardo demasiado en responder. Intenta nuevamente.";
    if (typeof status === "number" && status >= 500) return "Servicio temporalmente no disponible. Intenta mas tarde.";
    if (err.code === "ECONNABORTED") return "Tiempo de espera agotado al consultar la API.";
    if (err.code === "ECONNREFUSED" || err.code === "ENOTFOUND") return "No fue posible conectar con el servicio de CFDI.";
  }
  return "No fue posible procesar tu solicitud en este momento.";
}

function formatError(err) {
  if (axios.isAxiosError(err)) {
    return {
      message: err.message,
      code: err.code,
      status: err.response?.status,
      data: err.response?.data,
    };
  }
  return err?.stack || err?.message || String(err);
}

function formatObject(data) {
  if (!data || typeof data !== "object") {
    return String(data ?? "");
  }
  return Object.entries(data)
    .slice(0, 20)
    .map(([key, value]) => {
      if (Array.isArray(value)) return `- ${key}: [${value.length}]`;
      if (value && typeof value === "object") return `- ${key}: {..}`;
      return `- ${key}: ${value}`;
    })
    .join("\n");
}

function formatSummary(data) {
  if (!data || typeof data !== "object") return "Resumen: sin datos.";
  const year = data.year ?? "";
  const month = data.month ?? "";
  return [
    `Resumen ${year}-${String(month).padStart(2, "0")}`,
    `- ingresos_total_sin_iva: ${data.ingresos_total_sin_iva ?? "-"}`,
    `- iva_causado_sugerido: ${data.iva_causado_sugerido ?? "-"}`,
    `- iva_acreditable_sugerido: ${data.iva_acreditable_sugerido ?? "-"}`,
    `- iva_retenido_plat: ${data.iva_retenido_plat ?? "-"}`,
    `- iva_neto_sugerido: ${data.iva_neto_sugerido ?? "-"}`,
  ].join("\n");
}

function formatSummaryDetails(data) {
  if (!data || typeof data !== "object") return "Resumen detalle: sin datos.";
  const docs = Array.isArray(data.docs) ? data.docs.length : 0;
  const pagos = Array.isArray(data.pagos_rows) ? data.pagos_rows.length : 0;
  return `Resumen detalle:\n- docs: ${docs}\n- pagos: ${pagos}`;
}

function formatDeclaracionMode(data) {
  if (!data || typeof data !== "object") return "Modo declaracion: sin datos.";
  const year = data.year ?? "";
  const month = data.month ?? "";
  return [
    `Declaracion ${year}-${String(month).padStart(2, "0")}`,
    `- ingresos_total_sin_iva: ${data.ingresos_total_sin_iva ?? "-"}`,
    `- iva_trasladado_total: ${data.iva_trasladado_total ?? "-"}`,
    `- iva_retenido: ${data.iva_retenido ?? "-"}`,
    `- docs_count: ${data.docs_count ?? "-"}`,
    `- pagos_count: ${data.pagos_count ?? "-"}`,
    `- retenciones_count: ${data.retenciones_count ?? "-"}`,
  ].join("\n");
}

function isTransientNavigationError(err) {
  const text = String(err?.message || err || "").toLowerCase();
  return text.includes("execution context was destroyed") || text.includes("most likely because of a navigation");
}

function clearReadyWatchdog() {
  if (readyTimer) {
    clearTimeout(readyTimer);
    readyTimer = null;
  }
}

function armReadyWatchdog() {
  clearReadyWatchdog();
  readyTimer = setTimeout(async () => {
    if (hasLoggedReady || isRestarting) return;
    console.warn(`[WA] No llego a estado ready en ${READY_TIMEOUT_MS}ms. Reiniciando cliente...`);
    await restartClient("ready_timeout");
  }, READY_TIMEOUT_MS);
}

async function restartClient(reason) {
  if (isRestarting) return;
  isRestarting = true;
  clearReadyWatchdog();
  await setBotStatus("restarting", { linked: false, ready: false, reason });
  try {
    await client.destroy();
  } catch (err) {
    console.warn("[WA] Error al destruir cliente:", err?.message || err);
  }
  hasLoggedAuthenticated = false;
  hasLoggedReady = false;
  await sleep(1500);
  try {
    client.initialize();
    armReadyWatchdog();
  } finally {
    isRestarting = false;
  }
}

async function safeReply(msg, text, options) {
  try {
    await msg.reply(text, undefined, options);
    return;
  } catch (err) {
    console.warn("[WA] msg.reply fallo, usando fallback:", err?.message || err);
  }
  const to = msg?.from;
  if (to) {
    await client.sendMessage(to, text, options);
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function setBotStatus(status, extra = {}) {
  const payload = {
    status,
    linked: false,
    ready: false,
    updatedAt: new Date().toISOString(),
    ...extra,
  };
  try {
    await writeFile(STATUS_FILE, JSON.stringify(payload, null, 2), "utf-8");
  } catch (err) {
    console.error("No se pudo escribir archivo de estado:", err?.message || err);
  }
}

function loadEnvFile() {
  const envPath = resolve(process.cwd(), ".env");
  if (!existsSync(envPath)) {
    return;
  }
  try {
    const raw = readFileSync(envPath, "utf-8");
    for (const line of raw.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) {
        continue;
      }
      const idx = trimmed.indexOf("=");
      if (idx <= 0) {
        continue;
      }
      const key = trimmed.slice(0, idx).trim();
      const value = trimmed.slice(idx + 1).trim().replace(/^['"]|['"]$/g, "");
      if (!(key in process.env)) {
        process.env[key] = value;
      }
    }
  } catch (err) {
    console.warn("[WA] No se pudo cargar .env:", err?.message || err);
  }
}
