# CFDI MCP Server

Servidor MCP en Node que expone los endpoints de `cfdi_api` como tools.

## Requisitos

- Node.js 18+ (para `fetch`, `FormData` y `Blob`)
- API corriendo en `http://127.0.0.1:8000`

## Instalacion

```bash
cd c:\codigos_fuente\cfdi_app\cfdi-mcp-server
npm install
```

## Ejecutar

```bash
set CFDI_API_BASE=http://127.0.0.1:8000
set CFDI_FILES_ROOT=C:\cfdi\imports
npm start
```

## Variables de entorno

- `CFDI_API_BASE`: Base URL de la API (default `http://127.0.0.1:8000`)
- `CFDI_FILES_ROOT`: Carpeta permitida para subir archivos (obligatorio)
- `CFDI_API_TOKEN`: Token bearer para la API (opcional)
- `CFDI_API_TOKEN_FILE`: Ruta a archivo con el token (opcional, tiene prioridad si `CFDI_API_TOKEN` no existe)
- `CFDI_FETCH_TIMEOUT_MS`: Timeout por request (default `15000`)
- `CFDI_FETCH_MAX_BYTES`: Límite de bytes por respuesta (default `5242880`)

## Reglas de seguridad para archivos

- Solo 1 archivo por request.
- Extensiones permitidas: `.xml` y `.pdf`.
- Tamaño máximo: 8 MB.
- La ruta debe estar dentro de `CFDI_FILES_ROOT`.

## Configurar VS Code (MCP)

En `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "cfdi-api": {
        "command": "node",
        "args": ["c:\\codigos_fuente\\cfdi_app\\cfdi-mcp-server\\index.js"],
        "env": {
          "CFDI_API_BASE": "http://127.0.0.1:8000",
          "CFDI_FILES_ROOT": "C:\\cfdi\\imports"
        }
      }
    }
  }
}
```

## Configurar Claude Desktop (MCP)

En `%AppData%\\Claude\\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cfdi-mcp-server": {
      "command": "node",
      "args": ["C:\\codigos_fuente\\cfdi_app\\cfdi-mcp-server\\index.js"],
      "env": {
        "CFDI_API_BASE": "http://127.0.0.1:8000",
        "CFDI_FILES_ROOT": "C:\\cfdi\\imports",
        "CFDI_API_TOKEN_FILE": "C:\\cfdi\\secrets\\token.txt"
      }
    }
  }
}
```

## Tools disponibles

- `cfdi_health`
- `facturas_list`, `facturas_detail`, `facturas_xml` (requieren `rfc`)
- `deducciones_catalogo` (requiere `rfc` y `tipo_declaracion`)
- `retenciones_list`, `retenciones_detail` (requieren `rfc`)
- `declaraciones_list`, `declaraciones_detail`, `declaraciones_pdf`, `declaraciones_resumen` (requieren `rfc`)
- `reportes_summary`, `reportes_summary_details`, `reportes_declaracion_mode` (requieren `rfc`)
- `reportes_hoja_sat`, `reportes_sat_csv` (requieren `rfc`)
- `importar_xml`, `importar_pdf`

## Ejemplos de uso (MCP)

```json
{
  "name": "facturas_list",
  "arguments": {
    "rfc": "XAXX010101000",
    "year": 2024,
    "month": 12,
    "naturaleza": "gasto",
    "tipo_declaracion": "MENSUAL",
    "deducibilidad": "DEDUCIBLES"
  }
}
```

```json
{
  "name": "deducciones_catalogo",
  "arguments": {
    "rfc": "XAXX010101000",
    "tipo_declaracion": "MENSUAL"
  }
}
```

```json
{
  "name": "declaraciones_pdf",
  "arguments": {
    "rfc": "XAXX010101000",
    "dec_id": 123,
    "filename": "acuse.pdf"
  }
}
```

```json
{
  "name": "importar_xml",
  "arguments": {
    "file_paths": ["C:\\cfdi\\imports\\factura1.xml"]
  }
}
```
