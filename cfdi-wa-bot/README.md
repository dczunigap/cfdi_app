# CFDI WA Bot

Bot de WhatsApp que consulta la API CFDI.

## Requisitos

- Node.js 18+
- API corriendo en `http://127.0.0.1:8000`

## Instalacion

```bash
cd c:\codigos_fuente\cfdi_app\cfdi-wa-bot
npm install
```

## Variables de entorno

- `CFDI_API_BASE`: Base URL de la API (default `http://127.0.0.1:8000/api/v1`)
- `CFDI_API_TOKEN`: Token bearer para la API (opcional si tu API no requiere auth)
- `CFDI_API_TIMEOUT_MS`: Timeout de llamadas API en ms (default `15000`)
- `WA_COMMAND_COOLDOWN_MS`: Cooldown por usuario para comandos en ms (default `2500`)
- `WA_READY_TIMEOUT_MS`: Tiempo maximo para esperar estado ready antes de reiniciar (default `90000`)
- `WA_STATUS_FILE`: Ruta del archivo de estado del bot (default `bot-status.json`)
- `WA_ALLOW_FROM_ME_COMMANDS`: Permite comandos enviados por la misma cuenta (`true`/`false`, default `true`)

## Ejecutar

PowerShell (sesion actual):
```powershell
$env:CFDI_API_BASE="http://127.0.0.1:8000/api/v1"
$env:CFDI_API_TOKEN="TU_TOKEN"
$env:WA_STATUS_FILE="c:\codigos_fuente\cfdi_app\cfdi-wa-bot\bot-status.json"
npm start
```

CMD (sesion actual):
```cmd
set CFDI_API_BASE=http://127.0.0.1:8000/api/v1
set CFDI_API_TOKEN=TU_TOKEN
npm start
```

Persistente (usuario):
```powershell
setx CFDI_API_BASE "http://127.0.0.1:8000/api/v1"
setx CFDI_API_TOKEN "TU_TOKEN"
```
Luego reinicia la terminal o el servicio del bot para que tome el valor.

## Estado del bot

El archivo `bot-status.json` reporta estado operativo:

- `starting`, `waiting_qr`, `authenticated`, `loading`, `ready`, `restarting`, `disconnected`, `auth_failure`
- `linked`: indica si la sesion esta vinculada
- `ready`: indica si esta listo para recibir mensajes
