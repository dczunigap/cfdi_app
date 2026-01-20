# Administracion Contable SAT

Este repositorio contiene el backend y el frontend separados:

## Proyectos
- `cfdi-api/`: API en Python (FastAPI) con arquitectura hexagonal. Maneja la importacion de XML/PDF, el acceso a BD y la logica de reportes. Ver `cfdi-api/README.md`.
- `cfdi-ui/`: UI en Angular. Consume la API, presenta listados, filtros y dashboards. Ver `cfdi-ui/README.md`.
- `mcp-bridge/`: Servidor MCP en Node que expone los endpoints de `cfdi-api` como tools para clientes MCP (VS Code/Claude Desktop).

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
npm start
```

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
          "CFDI_API_BASE": "http://127.0.0.1:8000"
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
        "CFDI_API_BASE": "http://127.0.0.1:8000"
      }
    }
  }
}
```

## Notas
- Cada proyecto se ejecuta y se configura por separado.
- Revisa los README internos para instrucciones de instalacion y ejecucion.
