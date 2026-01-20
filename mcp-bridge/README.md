# CFDI API MCP Bridge

Servidor MCP en Node que expone los endpoints de `cfdi_api` como tools.

## Requisitos

- Node.js 18+ (para `fetch`, `FormData` y `Blob`)
- API corriendo en `http://127.0.0.1:8000`

## Instalacion

```bash
cd c:\codigos_fuente\cfdi_app\mcp-bridge
npm install
```

## Ejecutar

```bash
set CFDI_API_BASE=http://127.0.0.1:8000
npm start
```

## Configurar VS Code (MCP)

En `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "cfdi-api": {
        "command": "node",
        "args": ["c:\\codigos_fuente\\cfdi_app\\mcp-bridge\\index.js"],
        "env": {
          "CFDI_API_BASE": "http://127.0.0.1:8000"
        }
      }
    }
  }
}
```

## Tools disponibles

- `cfdi_health`
- `facturas_list`, `facturas_detail`, `facturas_xml`
- `retenciones_list`, `retenciones_detail`
- `declaraciones_list`, `declaraciones_detail`, `declaraciones_pdf`, `declaraciones_resumen`
- `reportes_summary`, `reportes_summary_details`, `reportes_declaracion_mode`
- `reportes_hoja_sat`, `reportes_sat_csv`
- `importar_xml`, `importar_pdf`
