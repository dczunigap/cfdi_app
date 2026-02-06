# Administracion Contable SAT

Este repositorio contiene el backend y el frontend separados:

## Proyectos
- `cfdi-api/`: API en Python (FastAPI) con arquitectura hexagonal. Maneja la importacion de XML/PDF, el acceso a BD y la logica de reportes. Ver `cfdi-api/README.md`.
- `cfdi-ui/`: UI en Angular. Consume la API, presenta listados, filtros y dashboards. Ver `cfdi-ui/README.md`.
- `cfdi-admin-ui/`: UI en Next.js para administracion de usuarios y catalogos SAT (incluye Admin SAT y Platform RFCs). Ver `cfdi-admin-ui/README.md`.
- `mcp-bridge/`: Servidor MCP en Node que expone los endpoints de `cfdi-api` como tools para clientes MCP (VS Code/Claude Desktop). Ver `mcp-bridge/README.md`.
- `wa-bot/`: Bot de WhatsApp en Node para integraciones y automatizaciones relacionadas con el flujo CFDI. Ver `wa-bot/README.md`.

## Wa-bot
Bot de WhatsApp para integraciones y automatizaciones.

### Requisitos
- Node.js 18+

### Instalacion
```bash
cd wa-bot
npm install
```

### Ejecucion
```bash
node index.js
```

### Notas de configuracion
- Variable `CFDI_API_BASE`: URL base del API (por defecto `http://127.0.0.1:8000/api/v1`).
- Variable `CFDI_API_TOKEN`: Token bearer para la API (si el backend requiere auth).
- Al iniciar por primera vez, se muestra un QR en consola; escanealo con WhatsApp para autorizar la sesion.

## MCP Bridge (tools)
Bridge MCP para exponer los endpoints del API sin cambios en `cfdi-api`.

### Requisitos
- Node.js 18+
- `cfdi-api` corriendo en `http://127.0.0.1:8000`

### Instalacion
```bash
cd mcp-bridge
npm install
```

### Ejecucion
```bash
set CFDI_API_BASE=http://127.0.0.1:8000
set CFDI_FILES_ROOT=C:\cfdi\imports
npm start
```

### Variables de entorno
- `CFDI_API_BASE`: Base URL del API (default `http://127.0.0.1:8000`)
- `CFDI_FILES_ROOT`: Carpeta permitida para subir archivos (obligatorio)
- `CFDI_API_TOKEN`: Token bearer para la API (opcional)
- `CFDI_API_TOKEN_FILE`: Ruta a archivo con el token (opcional)

### Configuracion VS Code
Archivo `.vscode/mcp.json`:
```json
{
  "mcp": {
    "servers": {
      "cfdi-api": {
        "command": "node",
        "args": ["c:\\\\codigos_fuente\\\\cfdi_app\\\\mcp-bridge\\\\index.js"],
        "env": {
          "CFDI_API_BASE": "http://127.0.0.1:8000",
          "CFDI_FILES_ROOT": "C:\\\\cfdi\\\\imports"
        }
      }
    }
  }
}
```

### Configuracion Claude Desktop
Archivo `C:\\Users\\dczun\\AppData\\Roaming\\Claude\\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "cfdi-api": {
      "command": "node",
      "args": ["C:\\\\codigos_fuente\\\\cfdi_app\\\\mcp-bridge\\\\index.js"],
      "env": {
        "CFDI_API_BASE": "http://127.0.0.1:8000",
        "CFDI_FILES_ROOT": "C:\\\\cfdi\\\\imports",
        "CFDI_API_TOKEN_FILE": "C:\\\\cfdi\\\\secrets\\\\token.txt"
      }
    }
  }
}
```

## Notas
- Cada proyecto se ejecuta y se configura por separado.
- Revisa los README internos para instrucciones de instalacion y ejecucion.
