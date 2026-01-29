# WA Bot (CFDI)

Bot de WhatsApp que consulta la API CFDI.

## Requisitos

- Node.js 18+
- API corriendo en `http://127.0.0.1:8000`

## Instalacion

```bash
cd c:\codigos_fuente\cfdi_app\wa-bot
npm install
```

## Variables de entorno

- `CFDI_API_BASE`: Base URL de la API (default `http://127.0.0.1:8000/api/v1`)
- `CFDI_API_TOKEN`: Token bearer para la API (opcional si tu API no requiere auth)

## Ejecutar

PowerShell (sesion actual):
```powershell
$env:CFDI_API_BASE="http://127.0.0.1:8000/api/v1"
$env:CFDI_API_TOKEN="TU_TOKEN"
node index.js
```

CMD (sesion actual):
```cmd
set CFDI_API_BASE=http://127.0.0.1:8000/api/v1
set CFDI_API_TOKEN=TU_TOKEN
node index.js
```

Persistente (usuario):
```powershell
setx CFDI_API_BASE "http://127.0.0.1:8000/api/v1"
setx CFDI_API_TOKEN "TU_TOKEN"
```
Luego reinicia la terminal o el servicio del bot para que tome el valor.
