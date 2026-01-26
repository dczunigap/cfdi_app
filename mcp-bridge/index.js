import { readFile } from "node:fs/promises";
import { basename } from "node:path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const BASE_URL = process.env.CFDI_API_BASE || "http://127.0.0.1:8000";

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
        year: { type: "integer" },
        month: { type: "integer" },
        tipo: { type: "string" },
        naturaleza: { type: "string" },
      },
    },
  },
  {
    name: "facturas_detail",
    description: "Detalle de factura por id.",
    inputSchema: {
      type: "object",
      properties: { factura_id: { type: "integer" } },
      required: ["factura_id"],
    },
  },
  {
    name: "facturas_xml",
    description: "XML de factura por id.",
    inputSchema: {
      type: "object",
      properties: { factura_id: { type: "integer" } },
      required: ["factura_id"],
    },
  },
  {
    name: "retenciones_list",
    description: "Lista retenciones (opcional: year, month).",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "integer" },
        month: { type: "integer" },
      },
    },
  },
  {
    name: "retenciones_detail",
    description: "Detalle de retencion por id.",
    inputSchema: {
      type: "object",
      properties: { retencion_id: { type: "integer" } },
      required: ["retencion_id"],
    },
  },
  {
    name: "declaraciones_list",
    description: "Lista declaraciones (opcional: year, month).",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "integer" },
        month: { type: "integer" },
      },
    },
  },
  {
    name: "declaraciones_detail",
    description: "Detalle de declaracion por id.",
    inputSchema: {
      type: "object",
      properties: { dec_id: { type: "integer" } },
      required: ["dec_id"],
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
      },
      required: ["dec_id", "filename"],
    },
  },
  {
    name: "declaraciones_resumen",
    description: "Resumen JSON de declaracion por id.",
    inputSchema: {
      type: "object",
      properties: { dec_id: { type: "integer" } },
      required: ["dec_id"],
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
      return await fetchJson("/api/v1/facturas", args);
    case "facturas_detail":
      return await fetchJson(`/api/v1/facturas/${args.factura_id}`);
    case "facturas_xml":
      return await fetchText(`/api/v1/facturas/${args.factura_id}/xml`);
    case "retenciones_list":
      return await fetchJson("/api/v1/retenciones", args);
    case "retenciones_detail":
      return await fetchJson(`/api/v1/retenciones/${args.retencion_id}`);
    case "declaraciones_list":
      return await fetchJson("/api/v1/declaraciones", args);
    case "declaraciones_detail":
      return await fetchJson(`/api/v1/declaraciones/${args.dec_id}`);
    case "declaraciones_pdf":
      return await fetchBinary(`/api/v1/declaraciones/${args.dec_id}/archivo/${args.filename}`);
    case "declaraciones_resumen":
      return await fetchJson(`/api/v1/declaraciones/${args.dec_id}/resumen.json`);
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

function buildHeaders(rfc) {
  if (!rfc) {
    return undefined;
  }
  return { "X-RFC": String(rfc).trim().toUpperCase() };
}

function stripRfc(args) {
  if (!args) {
    return args;
  }
  const { rfc, ...rest } = args;
  return rest;
}

async function fetchJson(path, query, rfc) {
  const res = await fetch(buildUrl(path, query), {
    headers: buildHeaders(rfc),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`${res.status}: ${text}`);
  }
  return { type: "text", text };
}

async function fetchText(path, query, rfc) {
  const res = await fetch(buildUrl(path, query), {
    headers: buildHeaders(rfc),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`${res.status}: ${text}`);
  }
  return { type: "text", text };
}

async function fetchBinary(path, query, rfc) {
  const res = await fetch(buildUrl(path, query), {
    headers: buildHeaders(rfc),
  });
  const buf = Buffer.from(await res.arrayBuffer());
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
  for (const filePath of filePaths) {
    const bytes = await readFile(filePath);
    form.append("files", new Blob([bytes]), basename(filePath));
  }
  const res = await fetch(buildUrl(path, query), {
    method: "POST",
    body: form,
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`${res.status}: ${text}`);
  }
  return { type: "text", text };
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
