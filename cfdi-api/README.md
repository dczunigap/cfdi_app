# cfdi-api
Backend Python (FastAPI) con arquitectura hexagonal ligera.

## Requisitos
- Python 3.10+

## Variables de entorno
- `CFDI_DB_URL` (default: `sqlite:///./data/contabilidad.sqlite`)
- `CFDI_AUTH_SECRET` (firma de tokens)
- `CFDI_AUTH_TTL_MINUTES` (minutos de vigencia del token, default 2880)
- `CFDI_AUTH_PBKDF2_ITER` (iteraciones de hashing, default 390000)
- `SAT_PASSWORD_SECRET` (clave Fernet para cifrado de PFX/password)
- `SAT_CFDI_AUTH_URL`
- `SAT_CFDI_SOLICITUD_URL`
- `SAT_CFDI_VERIFICACION_URL`
- `SAT_CFDI_DESCARGA_URL`
- `SAT_RET_AUTH_URL`
- `SAT_RET_SOLICITUD_URL`
- `SAT_RET_VERIFICACION_URL`
- `SAT_RET_DESCARGA_URL`
- `SAT_TIMEOUT_SECONDS`
- `SAT_SOAP_ACTION_DESCARGA`

## Instalacion (dev)
```
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar
```
uvicorn app.main:app --reload
```

## Pruebas (pytest)
```
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

Integracion SAT:
```
$env:PYTHONPATH = (Get-Location).Path
$env:RUN_SAT_INTEGRATION = "1"
python -m pytest -q
```

## Estructura
- `app/domain`: entidades y reglas puras
- `app/application`: casos de uso y DTOs
- `app/ports`: interfaces de salida
- `app/adapters`: inbound (HTTP) y outbound (DB/files)

## API
- Base: `/api/v1`
- OpenAPI: `GET /openapi.json`
- Header `X-RFC` requerido en endpoints SAT (auth) y reportes.
- Telefonos/RFC: `GET /rfc-phones/resolve?phone=...`, `POST /rfc-phones` para registrar.
- Auth: `POST /auth/login`, `POST /auth/register` (requiere auth), `POST /auth/logout`, `GET /auth/me`.
  - Nota: `POST /auth/register` permite bootstrap si no hay usuarios aún.
