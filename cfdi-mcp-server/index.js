import { readFile } from "node:fs/promises";
import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const BASE_URL = process.env.CFDI_API_BASE || "http://127.0.0.1:8000";
const FETCH_TIMEOUT_MS = Number(process.env.CFDI_FETCH_TIMEOUT_MS || 15000);
const FETCH_MAX_BYTES = Number(process.env.CFDI_FETCH_MAX_BYTES || 5 * 1024 * 1024);
const AUTH_TOKEN = process.env.CFDI_API_TOKEN || "";
const AUTH_TOKEN_FILE = process.env.CFDI_API_TOKEN_FILE || "";

const server = new McpServer({ name: "cfdi-mcp-server_v1", version: "0.1.0" });

const rfcSchema = z.string();
const monthSchema = z.number().int().min(1).max(12);
const yearSchema = z.number().int();

const tools = [
  {
    name: "cfdi_health",
    description: "Health check del API",
    inputSchema: z.object({}),
  },
  {
    name: "facturas_list",
    description: "Lista facturas (opcional: year, month, tipo, naturaleza).",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
      tipo: z.string().optional(),
      naturaleza: z.string().optional(),
    }),
  },
  {
    name: "facturas_detail",
    description: "Detalle de factura por id.",
    inputSchema: z.object({ factura_id: z.number().int(), rfc: rfcSchema }),
  },
  {
    name: "facturas_xml",
    description: "XML de factura por id.",
    inputSchema: z.object({ factura_id: z.number().int(), rfc: rfcSchema }),
  },
  {
    name: "retenciones_list",
    description: "Lista retenciones (opcional: year, month).",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
    }),
  },
  {
    name: "retenciones_detail",
    description: "Detalle de retencion por id.",
    inputSchema: z.object({ retencion_id: z.number().int(), rfc: rfcSchema }),
  },
  {
    name: "declaraciones_list",
    description: "Lista declaraciones (opcional: year, month).",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
    }),
  },
  {
    name: "declaraciones_detail",
    description: "Detalle de declaracion por id.",
    inputSchema: z.object({ dec_id: z.number().int(), rfc: rfcSchema }),
  },
  {
    name: "declaraciones_pdf",
    description: "Descarga PDF de declaracion por id y filename.",
    inputSchema: z.object({
      dec_id: z.number().int(),
      filename: z.string().min(1),
      rfc: rfcSchema,
    }),
  },
  {
    name: "declaraciones_resumen",
    description: "Resumen JSON de declaracion por id.",
    inputSchema: z.object({ dec_id: z.number().int(), rfc: rfcSchema }),
  },
  {
    name: "reportes_summary",
    description: "Resumen mensual (year, month). Requiere RFC.",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
    }),
  },
  {
    name: "reportes_summary_details",
    description: "Resumen mensual detalle (year, month). Requiere RFC.",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
    }),
  },
  {
    name: "reportes_declaracion_mode",
    description: "Modo declaracion (year, month, income_source). Requiere RFC.",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
      income_source: z.string().optional(),
    }),
  },
  {
    name: "reportes_hoja_sat",
    description: "Hoja SAT texto (year, month, income_source). Requiere RFC.",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
      income_source: z.string().optional(),
    }),
  },
  {
    name: "reportes_sat_csv",
    description: "Reporte SAT CSV (year, month, income_source). Requiere RFC.",
    inputSchema: z.object({
      rfc: rfcSchema,
      year: yearSchema.optional(),
      month: monthSchema.optional(),
      income_source: z.string().optional(),
    }),
  },
];

tools.forEach((tool) => {
  server.registerTool(
    tool.name,
    { description: tool.description, inputSchema: tool.inputSchema },
    async (args) => {
      try {
        const result = await handleTool(tool.name, args || {});
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
    }
  );
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
      throw new Error("Respuesta excede el limite permitido");
    }
    chunks.push(Buffer.from(value));
  }
  return Buffer.concat(chunks, total);
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport)
  .then(() => { console.error("Conectado al servidor"); })
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
