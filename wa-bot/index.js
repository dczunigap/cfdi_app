const { Client, LocalAuth, MessageMedia } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const axios = require("axios");

const API_BASE = process.env.CFDI_API_BASE || "http://127.0.0.1:8000/api/v1";
const API_TOKEN = process.env.CFDI_API_TOKEN || "";
const api = axios.create({ baseURL: API_BASE });

const client = new Client({
  authStrategy: new LocalAuth(),
  puppeteer: { headless: true },
  // webVersionCache: {
  //   type: 'remote',
  //   remotePath: 'https://raw.githubusercontent.com',
  // },
  markSeen: false
});

process.on("unhandledRejection", (err) => {
  console.error("UnhandledRejection:", err);
});
process.on("uncaughtException", (err) => {
  console.error("UncaughtException:", err);
});

client.on("qr", (qr) => qrcode.generate(qr, { small: true }));
client.on("ready", () => console.log("Bot listo"));

client.on("message", async (msg) => {
  if (!msg || typeof msg.body !== "string") {
    return;
  }
  if (msg.fromMe) {
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

  try {
    switch (cmd) {
      case "/help":
        await msg.reply(helpText());
        break;
      case "/facturas":
        await handleFacturas(msg, args);
        break;
      case "/facturas_rango":
        await handleFacturasRango(msg, args);
        break;
      case "/retenciones":
        await handleRetenciones(msg, args);
        break;
      case "/retenciones_rango":
        await handleRetencionesRango(msg, args);
        break;
      case "/declaraciones":
        await handleDeclaraciones(msg, args);
        break;
      case "/declaraciones_rango":
        await handleDeclaracionesRango(msg, args);
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
        await msg.reply("Comando no reconocido. Usa /help.");
        break;
    }
  } catch (err) {
    await msg.reply(`Error: ${err?.message || "fallo inesperado"}`);
  }
});

client.initialize();

function helpText() {
  return [
    "Comandos disponibles:",
    "/facturas <year> <month> [tipo] [naturaleza]",
    "/facturas_rango <year_from> <month_from> <year_to> <month_to> [tipo] [naturaleza]",
    "/retenciones <year> <month>",
    "/retenciones_rango <year_from> <month_from> <year_to> <month_to>",
    "/declaraciones <year> <month>",
    "/declaraciones_rango <year_from> <month_from> <year_to> <month_to>",
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
  const [year, month, tipo, naturaleza] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/facturas", {
    params: { year, month, tipo, naturaleza },
    headers: buildHeaders(rfc),
  });
  const items = res.data || [];
  if (!items.length) {
    await msg.reply("Sin facturas para ese periodo.");
    return;
  }
  const lines = items.slice(0, 5).map((f) => {
    const total = f.total || f.total_mxn || "";
    return `- ${f.uuid} | ${total} | ${f.emisor_rfc || ""}`;
  });
  await msg.reply(`Facturas (${items.length}):\n${lines.join("\n")}`);
}

async function handleFacturasRango(msg, args) {
  const [yearFrom, monthFrom, yearTo, monthTo, tipo, naturaleza] = args;
  if (!yearFrom || !monthFrom || !yearTo || !monthTo) {
    await msg.reply("Uso: /facturas_rango <year_from> <month_from> <year_to> <month_to>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const from = `${yearFrom}-${String(monthFrom).padStart(2, "0")}`;
  const to = `${yearTo}-${String(monthTo).padStart(2, "0")}`;
  const res = await api.get("/facturas", { headers: buildHeaders(rfc) });
  let items = res.data || [];
  items = items.filter((f) => {
    const key = `${f.year}-${String(f.month).padStart(2, "0")}`;
    return key >= from && key <= to;
  });
  if (tipo) {
    items = items.filter((f) => String(f.tipo || f.tipo_comprobante || "").toUpperCase() === tipo.toUpperCase());
  }
  if (naturaleza) {
    items = items.filter((f) => String(f.naturaleza || "").toLowerCase() === naturaleza.toLowerCase());
  }
  const lines = items.slice(0, 5).map((f) => {
    const total = f.total || f.total_mxn || "";
    return `- ${f.uuid} | ${total} | ${f.emisor_rfc || ""}`;
  });
  await msg.reply(
    items.length
      ? `Facturas (${items.length}) [${from}..${to}]:\n${lines.join("\n")}`
      : `Sin facturas en rango ${from}..${to}.`
  );
}
async function handleRetenciones(msg, args) {
  const [year, month] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/retenciones", {
    params: { year, month },
    headers: buildHeaders(rfc),
  });
  const items = res.data || [];
  if (!items.length) {
    await msg.reply("Sin retenciones para ese periodo.");
    return;
  }
  const lines = items.slice(0, 5).map((r) => {
    return `- ${r.uuid || r.id} | ${r.emisor_rfc || ""} -> ${r.receptor_rfc || ""}`;
  });
  await msg.reply(`Retenciones (${items.length}):\n${lines.join("\n")}`);
}

async function handleRetencionesRango(msg, args) {
  const [yearFrom, monthFrom, yearTo, monthTo] = args;
  if (!yearFrom || !monthFrom || !yearTo || !monthTo) {
    await msg.reply("Uso: /retenciones_rango <year_from> <month_from> <year_to> <month_to>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const from = `${yearFrom}-${String(monthFrom).padStart(2, "0")}`;
  const to = `${yearTo}-${String(monthTo).padStart(2, "0")}`;
  const res = await api.get("/retenciones", { headers: buildHeaders(rfc) });
  const items = res.data || [];
  const filtered = items.filter((r) => {
    const key = `${r.year}-${String(r.month).padStart(2, "0")}`;
    return key >= from && key <= to;
  });
  const lines = filtered.slice(0, 5).map((r) => {
    return `- ${r.uuid || r.id} | ${r.emisor_rfc || ""} -> ${r.receptor_rfc || ""}`;
  });
  await msg.reply(
    filtered.length
      ? `Retenciones (${filtered.length}) [${from}..${to}]:\n${lines.join("\n")}`
      : `Sin retenciones en rango ${from}..${to}.`
  );
}

async function handleDeclaraciones(msg, args) {
  const [year, month] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/declaraciones", {
    params: { year, month },
    headers: buildHeaders(rfc),
  });
  const items = res.data || [];
  if (!items.length) {
    await msg.reply("Sin declaraciones para ese periodo.");
    return;
  }
  const lines = items.slice(0, 5).map((d) => {
    return `- id:${d.id} | ${d.rfc || ""} | ${d.folio || ""}`;
  });
  await msg.reply(`Declaraciones (${items.length}):\n${lines.join("\n")}`);
}

async function handleDeclaracionesRango(msg, args) {
  const [yearFrom, monthFrom, yearTo, monthTo] = args;
  if (!yearFrom || !monthFrom || !yearTo || !monthTo) {
    await msg.reply("Uso: /declaraciones_rango <year_from> <month_from> <year_to> <month_to>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const from = `${yearFrom}-${String(monthFrom).padStart(2, "0")}`;
  const to = `${yearTo}-${String(monthTo).padStart(2, "0")}`;
  const res = await api.get("/declaraciones", { headers: buildHeaders(rfc) });
  const items = res.data || [];
  const filtered = items.filter((d) => {
    const key = `${d.year}-${String(d.month).padStart(2, "0")}`;
    return key >= from && key <= to;
  });
  const lines = filtered.slice(0, 5).map((d) => {
    return `- id:${d.id} | ${d.rfc || ""} | ${d.folio || ""}`;
  });
  await msg.reply(
    filtered.length
      ? `Declaraciones (${filtered.length}) [${from}..${to}]:\n${lines.join("\n")}`
      : `Sin declaraciones en rango ${from}..${to}.`
  );
}
async function handleFacturaDetail(msg, args) {
  const [facturaId] = args;
  if (!facturaId) {
    await msg.reply("Uso: /factura <factura_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get(`/facturas/${facturaId}`, { headers: buildHeaders(rfc) });
  await msg.reply(`Factura ${facturaId}:\n${formatObject(res.data)}`);
}

async function handleFacturaXml(msg, args) {
  const [facturaId] = args;
  if (!facturaId) {
    await msg.reply("Uso: /factura_xml <factura_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get(`/facturas/${facturaId}/xml`, { headers: buildHeaders(rfc) });
  const text = res.data || "";
  const preview = text.length > 3500 ? text.slice(0, 3500) + "\n...[truncado]" : text;
  await msg.reply(preview || "XML vacio.");
}

async function handleDeclaracionPdf(msg, args) {
  const [decId, filename] = args;
  if (!decId || !filename) {
    await msg.reply("Uso: /declaracion_pdf <dec_id> <filename>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get(`/declaraciones/${decId}/archivo/${filename}`, {
    responseType: "arraybuffer",
    headers: buildHeaders(rfc),
  });
  const data = Buffer.from(res.data);
  const media = new MessageMedia("application/pdf", data.toString("base64"), filename);
  await msg.reply(media, undefined, { sendMediaAsDocument: true });
}

async function handleRetencionDetail(msg, args) {
  const [retencionId] = args;
  if (!retencionId) {
    await msg.reply("Uso: /retencion <retencion_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get(`/retenciones/${retencionId}`, { headers: buildHeaders(rfc) });
  await msg.reply(`Retencion ${retencionId}:\n${formatObject(res.data)}`);
}

async function handleDeclaracionResumen(msg, args) {
  const [decId] = args;
  if (!decId) {
    await msg.reply("Uso: /declaracion_resumen <dec_id>");
    return;
  }
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get(`/declaraciones/${decId}/resumen.json`, { headers: buildHeaders(rfc) });
  await msg.reply(`Resumen declaracion ${decId}:\n${formatObject(res.data)}`);
}

async function handleSummary(msg, args) {
  const [year, month] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/summary", {
    params: { year, month },
    headers: buildHeaders(rfc),
  });
  await msg.reply(formatSummary(res.data));
}

async function handleSummaryDetails(msg, args) {
  const [year, month] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/summary/details", {
    params: { year, month },
    headers: buildHeaders(rfc),
  });
  await msg.reply(formatSummaryDetails(res.data));
}

async function handleDeclaracionMode(msg, args) {
  const [year, month, income_source] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/declaracion", {
    params: { year, month, income_source: income_source || "auto" },
    headers: buildHeaders(rfc),
  });
  await msg.reply(formatDeclaracionMode(res.data));
}

async function handleHojaSat(msg, args) {
  const [year, month, income_source] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/sat_hoja.txt", {
    params: { year, month, income_source: income_source || "auto" },
    headers: buildHeaders(rfc),
  });
  await msg.reply(res.data || "Sin respuesta.");
}

async function handleSatCsv(msg, args) {
  const [year, month, income_source] = args;
  const rfc = await requireRfc(msg);
  if (!rfc) {
    return;
  }
  const res = await api.get("/sat_report.csv", {
    params: { year, month, income_source: income_source || "auto" },
    headers: buildHeaders(rfc),
  });
  const lines = (res.data || "").split("\n").slice(0, 6).join("\n");
  await msg.reply(`CSV (primeras lineas):\n${lines}`);
}

function normalizePhone(value) {
  return String(value || "").replace(/\D+/g, "");
}

function buildHeaders(rfc) {
  const headers = {
    "X-RFC": String(rfc || "").trim().toUpperCase(),
  };
  if (API_TOKEN) {
    headers.Authorization = `Bearer ${API_TOKEN}`;
  }
  return headers;
}

async function requireRfc(msg) {
  const phone = normalizePhone(msg.author || msg.from);
  if (!phone) {
    await msg.reply("No pude identificar tu telefono para resolver el RFC.");
    return null;
  }
  try {
    const res = await api.get("/rfc-phones/resolve", { params: { phone } });
    const rfc = res.data?.rfc;
    if (!rfc) {
      await msg.reply("No hay RFC asociado a tu telefono. Pide al admin que lo registre.");
      return null;
    }
    return rfc;
  } catch (err) {
    if (err?.response?.status === 404) {
      await msg.reply("Telefono no registrado. Pide al admin que lo registre con tu RFC.");
      return null;
    }
    throw err;
  }
}

function formatJson(data) {
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return String(data);
  }
}

function formatObject(data) {
  if (!data || typeof data !== "object") {
    return String(data ?? "");
  }
  const entries = Object.entries(data).slice(0, 20);
  return entries
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `- ${key}: [${value.length}]`;
      }
      if (value && typeof value === "object") {
        return `- ${key}: {..}`;
      }
      return `- ${key}: ${value}`;
    })
    .join("\n");
}

function formatSummary(data) {
  if (!data || typeof data !== "object") {
    return "Resumen: sin datos.";
  }
  const year = data.year ?? "";
  const month = data.month ?? "";
  const lines = [
    `Resumen ${year}-${String(month).padStart(2, "0")}`,
    `- ingresos_total_sin_iva: ${data.ingresos_total_sin_iva ?? "-"}`,
    `- iva_causado_sugerido: ${data.iva_causado_sugerido ?? "-"}`,
    `- iva_acreditable_sugerido: ${data.iva_acreditable_sugerido ?? "-"}`,
    `- iva_retenido_plat: ${data.iva_retenido_plat ?? "-"}`,
    `- iva_neto_sugerido: ${data.iva_neto_sugerido ?? "-"}`,
  ];
  return lines.join("\n");
}

function formatSummaryDetails(data) {
  if (!data || typeof data !== "object") {
    return "Resumen detalle: sin datos.";
  }
  const docs = Array.isArray(data.docs) ? data.docs.length : 0;
  const pagos = Array.isArray(data.pagos_rows) ? data.pagos_rows.length : 0;
  return `Resumen detalle:\n- docs: ${docs}\n- pagos: ${pagos}`;
}

function formatDeclaracionMode(data) {
  if (!data || typeof data !== "object") {
    return "Modo declaracion: sin datos.";
  }
  const year = data.year ?? "";
  const month = data.month ?? "";
  const lines = [
    `Declaracion ${year}-${String(month).padStart(2, "0")}`,
    `- ingresos_total_sin_iva: ${data.ingresos_total_sin_iva ?? "-"}`,
    `- iva_trasladado_total: ${data.iva_trasladado_total ?? "-"}`,
    `- iva_retenido: ${data.iva_retenido ?? "-"}`,
    `- docs_count: ${data.docs_count ?? "-"}`,
    `- pagos_count: ${data.pagos_count ?? "-"}`,
    `- retenciones_count: ${data.retenciones_count ?? "-"}`,
  ];
  return lines.join("\n");
}
