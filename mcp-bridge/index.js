import { readFile, stat } from "node:fs/promises";
import { basename, extname, resolve, sep } from "node:path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const BASE_URL = process.env.CFDI_API_BASE || "http://127.0.0.1:8000";
const FILES_ROOT = process.env.CFDI_FILES_ROOT || "";
const FETCH_TIMEOUT_MS = Number(process.env.CFDI_FETCH_TIMEOUT_MS || 15000);
const FETCH_MAX_BYTES = Number(process.env.CFDI_FETCH_MAX_BYTES || 5 * 1024 * 1024);
const AUTH_TOKEN = process.env.CFDI_API_TOKEN || "";
const AUTH_TOKEN_FILE = process.env.CFDI_API_TOKEN_FILE || "";
const MAX_FILES = 1;
const MAX_FILE_BYTES = 8 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set([".xml", ".pdf"]);
const RFC_REGEX = /^[A-Z&]{3,4}\d{6}[A-Z0-9]{3}$/;

const server = new Server(
  { name: "cfdi-api-bridge", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

const tools = [
  {
    name: "cfdi_health",
    description: "Health check del API",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "facturas_list",
    description: "Lista facturas (opcional: year, month, tipo, naturaleza).",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
        tipo: { type: "string" },
        naturaleza: { type: "string" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "facturas_detail",
    description: "Detalle de factura por id.",
    inputSchema: {
      type: "object",
      properties: { factura_id: { type: "integer" }, rfc: { type: "string" } },
      required: ["factura_id", "rfc"],
    },
  },
  {
    name: "facturas_xml",
    description: "XML de factura por id.",
    inputSchema: {
      type: "object",
      properties: { factura_id: { type: "integer" }, rfc: { type: "string" } },
      required: ["factura_id", "rfc"],
    },
  },
  {
    name: "retenciones_list",
    description: "Lista retenciones (opcional: year, month).",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "retenciones_detail",
    description: "Detalle de retencion por id.",
    inputSchema: {
      type: "object",
      properties: { retencion_id: { type: "integer" }, rfc: { type: "string" } },
      required: ["retencion_id", "rfc"],
    },
  },
  {
    name: "declaraciones_list",
    description: "Lista declaraciones (opcional: year, month).",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "declaraciones_detail",
    description: "Detalle de declaracion por id.",
    inputSchema: {
      type: "object",
      properties: { dec_id: { type: "integer" }, rfc: { type: "string" } },
      required: ["dec_id", "rfc"],
    },
  },
  {
    name: "declaraciones_pdf",
    description: "Descarga PDF de declaracion por id y filename.",
    inputSchema: {
      type: "object",
      properties: {
        dec_id: { type: "integer" },
        filename: { type: "string" },
        rfc: { type: "string" },
      },
      required: ["dec_id", "filename", "rfc"],
    },
  },
  {
    name: "declaraciones_resumen",
    description: "Resumen JSON de declaracion por id.",
    inputSchema: {
      type: "object",
      properties: { dec_id: { type: "integer" }, rfc: { type: "string" } },
      required: ["dec_id", "rfc"],
    },
  },
  {
    name: "reportes_summary",
    description: "Resumen mensual (year, month). Requiere RFC.",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "reportes_summary_details",
    description: "Resumen mensual detalle (year, month). Requiere RFC.",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "reportes_declaracion_mode",
    description: "Modo declaracion (year, month, income_source). Requiere RFC.",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
        income_source: { type: "string" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "reportes_hoja_sat",
    description: "Hoja SAT texto (year, month, income_source). Requiere RFC.",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
        income_source: { type: "string" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "reportes_sat_csv",
    description: "Reporte SAT CSV (year, month, income_source). Requiere RFC.",
    inputSchema: {
      type: "object",
      properties: {
        rfc: { type: "string" },
        year: { type: "integer" },
        month: { type: "integer" },
        income_source: { type: "string" },
      },
      required: ["rfc"],
    },
  },
  {
    name: "importar_xml",
    description: "Importa XML. Envía rutas de archivos locales.",
    inputSchema: {
      type: "object",
      properties: {
        file_paths: { type: "array", items: { type: "string" } },
      },
      required: ["file_paths"],
    },
  },
  {
    name: "importar_pdf",
    description: "Importa PDF. Envía rutas de archivos locales (opcional year/month).",
    inputSchema: {
      type: "object",
      properties: {
        file_paths: { type: "array", items: { type: "string" } },
        year: { type: "integer" },
        month: { type: "integer" },
      },
      required: ["file_paths"],
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools,
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    const result = await handleTool(name, args || {});
    return { content: [result] };
  } catch (err) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${err?.message || String(err)}`,
        },
      ],
      isError: true,
    };
  }
});

async function handleTool(name, args) {
  const cleanArgs = stripRfc(args || {});
  switch (name) {
    case "cfdi_health":
      return await fetchJson("/api/v1/");
    case "facturas_list":
      return await fetchJson("/api/v1/facturas", cleanArgs, args.rfc);
    case "facturas_detail":
      return await fetchJson(`/api/v1/facturas/${args.factura_id}`, null, args.rfc);
    case "facturas_xml":
      return await fetchText(`/api/v1/facturas/${args.factura_id}/xml`, null, args.rfc);
    case "retenciones_list":
      return await fetchJson("/api/v1/retenciones", cleanArgs, args.rfc);
    case "retenciones_detail":
      return await fetchJson(`/api/v1/retenciones/${args.retencion_id}`, null, args.rfc);
    case "declaraciones_list":
      return await fetchJson("/api/v1/declaraciones", cleanArgs, args.rfc);
    case "declaraciones_detail":
      return await fetchJson(`/api/v1/declaraciones/${args.dec_id}`, null, args.rfc);
    case "declaraciones_pdf":
      return await fetchBinary(
        `/api/v1/declaraciones/${args.dec_id}/archivo/${args.filename}`,
        null,
        args.rfc
      );
    case "declaraciones_resumen":
      return await fetchJson(`/api/v1/declaraciones/${args.dec_id}/resumen.json`, null, args.rfc);
    case "reportes_summary":
      return await fetchJson("/api/v1/summary", cleanArgs, args.rfc);
    case "reportes_summary_details":
      return await fetchJson("/api/v1/summary/details", cleanArgs, args.rfc);
    case "reportes_declaracion_mode":
      return await fetchJson("/api/v1/declaracion", cleanArgs, args.rfc);
    case "reportes_hoja_sat":
      return await fetchText("/api/v1/sat_hoja.txt", cleanArgs, args.rfc);
    case "reportes_sat_csv":
      return await fetchText("/api/v1/sat_report.csv", cleanArgs, args.rfc);
    case "importar_xml":
      return await postFiles("/api/v1/importar", args.file_paths, null);
    case "importar_pdf":
      return await postFiles("/api/v1/importar_pdf", args.file_paths, {
        year: args.year,
        month: args.month,
      });
    default:
      throw new Error(`Tool no soportado: ${name}`);
  }
}

function buildUrl(path, query) {
  const url = new URL(path, BASE_URL);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }
      url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
}

async function buildHeaders(rfc) {
  const headers = {};
  const normalized = normalizeRfc(rfc);
  if (normalized) {
    headers["X-RFC"] = normalized;
  }
  const token = await getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return Object.keys(headers).length ? headers : undefined;
}

function stripRfc(args) {
  if (!args) {
    return args;
  }
  const { rfc, ...rest } = args;
  return rest;
}

function normalizeRfc(rfc) {
  if (!rfc) {
    return undefined;
  }
  const cleaned = String(rfc).trim().toUpperCase();
  if (!RFC_REGEX.test(cleaned)) {
    throw new Error("RFC inválido");
  }
  return cleaned;
}

async function fetchJson(path, query, rfc) {
  const res = await fetchWithTimeout(buildUrl(path, query), {
    headers: await buildHeaders(rfc),
  });
  const text = await readTextWithLimit(res);
  if (!res.ok) {
    throw new Error(`${res.status}: ${text}`);
  }
  return { type: "text", text };
}

async function fetchText(path, query, rfc) {
  const res = await fetchWithTimeout(buildUrl(path, query), {
    headers: await buildHeaders(rfc),
  });
  const text = await readTextWithLimit(res);
  if (!res.ok) {
    throw new Error(`${res.status}: ${text}`);
  }
  return { type: "text", text };
}

async function fetchBinary(path, query, rfc) {
  const res = await fetchWithTimeout(buildUrl(path, query), {
    headers: await buildHeaders(rfc),
  });
  const buf = await readBufferWithLimit(res);
  if (!res.ok) {
    throw new Error(`${res.status}: ${buf.toString("utf-8")}`);
  }
  return {
    type: "text",
    text: JSON.stringify(
      {
        contentType: res.headers.get("content-type") || "application/octet-stream",
        base64: buf.toString("base64"),
      },
      null,
      2
    ),
  };
}

async function postFiles(path, filePaths, query) {
  const form = new FormData();
  const files = await validateFilePaths(filePaths);
  for (const file of files) {
    const bytes = await readFile(file.safePath);
    form.append("files", new Blob([bytes]), basename(file.originalPath));
  }
  const res = await fetchWithTimeout(buildUrl(path, query), {
    method: "POST",
    headers: await buildHeaders(null),
    body: form,
  });
  const text = await readTextWithLimit(res);
  if (!res.ok) {
    throw new Error(`${res.status}: ${text}`);
  }
  return { type: "text", text };
}

function resolveSafePath(p) {
  if (!FILES_ROOT) {
    throw new Error("FILES_ROOT no configurado");
  }
  const absRoot = resolve(FILES_ROOT);
  const absPath = resolve(p);
  const rootLower = (absRoot + sep).toLowerCase();
  if (!absPath.toLowerCase().startsWith(rootLower)) {
    throw new Error("Ruta de archivo fuera del directorio permitido");
  }
  return absPath;
}

async function getAuthToken() {
  if (AUTH_TOKEN) {
    return AUTH_TOKEN;
  }
  if (!AUTH_TOKEN_FILE) {
    return "";
  }
  try {
    const token = await readFile(AUTH_TOKEN_FILE, "utf-8");
    return token.trim();
  } catch (err) {
    throw new Error("No se pudo leer CFDI_API_TOKEN_FILE");
  }
}

function validateExtension(filePath) {
  const ext = extname(filePath).toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    throw new Error("Extensión de archivo no permitida");
  }
}

async function validateFilePaths(filePaths) {
  if (!Array.isArray(filePaths)) {
    throw new Error("file_paths debe ser un arreglo");
  }
  if (filePaths.length !== MAX_FILES) {
    throw new Error(`Solo se permite ${MAX_FILES} archivo por request`);
  }
  const results = [];
  for (const filePath of filePaths) {
    if (typeof filePath !== "string" || !filePath.trim()) {
      throw new Error("file_path inválido");
    }
    validateExtension(filePath);
    const safePath = resolveSafePath(filePath);
    const info = await stat(safePath);
    if (info.size > MAX_FILE_BYTES) {
      throw new Error("El archivo excede el tamaño máximo permitido");
    }
    results.push({ safePath, originalPath: filePath });
  }
  return results;
}

async function fetchWithTimeout(url, options) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function readTextWithLimit(res) {
  const buf = await readBufferWithLimit(res);
  return buf.toString("utf-8");
}

async function readBufferWithLimit(res) {
  const reader = res.body?.getReader();
  if (!reader) {
    return Buffer.from(await res.arrayBuffer());
  }
  let total = 0;
  const chunks = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.length;
    if (total > FETCH_MAX_BYTES) {
      throw new Error("Respuesta excede el límite permitido");
    }
    chunks.push(Buffer.from(value));
  }
  return Buffer.concat(chunks, total);
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
