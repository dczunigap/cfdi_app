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
- `CFDI_API_TOKEN`: Token bearer estatico para la API (opcional)
- `CFDI_API_EMAIL`: Usuario (email) para `POST /auth/login` (opcional, recomendado)
- `CFDI_API_PASSWORD`: Password para `POST /auth/login` (opcional, recomendado)
- `CFDI_API_AUTH_SKEW_MS`: Margen para renovar token antes de expirar (default `120000`)
- `CFDI_API_TIMEOUT_MS`: Timeout de llamadas API en ms (default `15000`)
- `WA_COMMAND_COOLDOWN_MS`: Cooldown por usuario para comandos en ms (default `2500`)
- `WA_READY_TIMEOUT_MS`: Tiempo maximo para esperar estado ready antes de reiniciar (default `90000`)
- `WA_STATUS_FILE`: Ruta del archivo de estado del bot (default `bot-status.json`)
- `WA_ALLOW_FROM_ME_COMMANDS`: Permite comandos enviados por la misma cuenta (`true`/`false`, default `true`)

## Como se envia X-RFC

El bot **no pide RFC por comando**. Lo resuelve asi:

1. Toma el telefono de WhatsApp del remitente.
2. Consulta `GET /rfc-phones/resolve?phone=<telefono>`.
3. Usa el RFC obtenido para enviar el header `X-RFC` en cada request a CFDI API.

Si `rfc-phones` no tiene ese telefono, el bot no puede construir `X-RFC` y responde pidiendo registro al admin.
El bot usa `msg.author/msg.from` y fallback `msg.getContact().number` para identificar telefono.

## Auth recomendada (login + refresh)

Si configuras `CFDI_API_EMAIL` y `CFDI_API_PASSWORD`, el bot:

1. Hace login en arranque (`POST /auth/login`).
2. Usa `refresh_token` (`POST /auth/refresh`) cuando el access token esta por expirar o recibe 401.
3. Reintenta automaticamente la llamada original al API.

## Uso recomendado con .env

1. Copia `cfdi-wa-bot/.env.example` a `cfdi-wa-bot/.env`.
2. Llena `CFDI_API_EMAIL` / `CFDI_API_PASSWORD` (o `CFDI_API_TOKEN`) y el resto de variables.
3. Ejecuta `npm start`.

## Ejecutar

PowerShell (sesion actual):
```powershell
$env:CFDI_API_BASE="http://127.0.0.1:8000/api/v1"
$env:CFDI_API_EMAIL="admin@example.com"
$env:CFDI_API_PASSWORD="demo123"
$env:WA_STATUS_FILE="c:\codigos_fuente\cfdi_app\cfdi-wa-bot\bot-status.json"
npm start
```

CMD (sesion actual):
```cmd
set CFDI_API_BASE=http://127.0.0.1:8000/api/v1
set CFDI_API_EMAIL=admin@example.com
set CFDI_API_PASSWORD=demo123
npm start
```

Persistente (usuario):
```powershell
setx CFDI_API_BASE "http://127.0.0.1:8000/api/v1"
setx CFDI_API_EMAIL "admin@example.com"
setx CFDI_API_PASSWORD "demo123"
```
Luego reinicia la terminal o el servicio del bot para que tome el valor.

## Estado del bot

El archivo `bot-status.json` reporta estado operativo:

- `starting`, `waiting_qr`, `authenticated`, `loading`, `ready`, `restarting`, `disconnected`, `auth_failure`
- `linked`: indica si la sesion esta vinculada
- `ready`: indica si esta listo para recibir mensajes
