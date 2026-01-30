# cfdi-api
Backend Python (FastAPI) con arquitectura hexagonal ligera.

## Requisitos
- Python 3.10+

## Variables de entorno
- `CFDI_DB_URL` (default: `sqlite:///./data/contabilidad.sqlite`)
- `CFDI_AUTH_SECRET` (firma de tokens)
- `CFDI_AUTH_TTL_MINUTES` (minutos de vigencia del token, default 2880)
- `CFDI_AUTH_PASSWORD_ITERATIONS` (iteraciones de hashing, default 390000)
- `SAT_PASSWORD_SECRET` (clave Fernet para cifrado de PFX/password)
- `SAT_ENV` (`uat` o `prod`, default `uat`)
- `CFDI_TIMEOUT_SAT_SECONDS`
- `SAT_DOWNLOAD_DIR` (ruta local para ZIPs, default `C:\cfdi\xml`)
- `REDIS_URL` (RQ broker, default `redis://localhost:6379/0`)
- `SAT_GATEWAY_MODE` (`soap` o `mock`, default `soap`)
- `SAT_AUTOVERIFY` (`1`/`0`, default `1`)
- `SAT_STORAGE_BACKEND` (`fs` o `r2`, default `fs`)
- `R2_ENDPOINT`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_REGION`

Tip: usa `cfdi-api/.env.example` como plantilla y ajusta `SAT_ENV` si quieres alternar UAT/PROD sin tocar código.
Nota: los endpoints SAT se toman exclusivamente de `SAT_ENDPOINTS`; no hay overrides por URL.

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

## Check rapido de endpoints SAT
```
$env:SAT_ENV = "uat"
python -c "from app.core.config import settings; print(settings.sat_cfdi_auth_url); print(settings.sat_ret_auth_url)"
```

```
$env:SAT_ENV = "prod"
python -c "from app.core.config import settings; print(settings.sat_cfdi_auth_url); print(settings.sat_ret_auth_url)"
```

## Pruebas (pytest)
```
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -vv --basetemp .tmp
```

Integracion SAT:
```
$env:PYTHONPATH = (Get-Location).Path
$env:RUN_SAT_INTEGRATION = "1"
python -m pytest -vv --basetemp .tmp
```

## RQ (jobs SAT)
Worker:
```
rq worker --url redis://localhost:6379/0
```

Flujo:
- `POST /api/v1/sat/descargas` crea solicitud y hace verificacion inicial.
- RQ reintenta verificacion y dispara descarga cuando esta LISTA.

Si quieres verificacion manual:
```
$env:SAT_AUTOVERIFY = "0"
```
Luego puedes llamar:
`POST /api/v1/sat/descargas/{id}/verify`

Nota (Python 3.14): `redis`/`rq` pueden no estar disponibles. En ese caso usa
`SAT_AUTOVERIFY=0` y el endpoint manual de verificacion.

## Modo mock (sin SAT real)
```
$env:SAT_GATEWAY_MODE = "mock"
$env:PYTHONPATH = (Get-Location).Path
$env:RUN_SAT_INTEGRATION = "1"
python -m pytest -q --basetemp .tmp tests/integration/test_sat_solicitud.py
```
Esto usa un gateway fake que devuelve ZIPs con XML de ejemplo.

## Storage R2 (MinIO local)
```
$env:SAT_STORAGE_BACKEND = "r2"
$env:R2_ENDPOINT = "http://127.0.0.1:9000"
$env:R2_ACCESS_KEY = "minioadmin"
$env:R2_SECRET_KEY = "minioadmin"
$env:R2_BUCKET = "cfdi-zip"
$env:R2_REGION = "auto"
```

Antes de correr tests R2:
- Asegura MinIO corriendo: `minio server C:\minio-data --console-address ":9001"`
- Crea el bucket:
  - `mc alias set myminio http://127.0.0.1:9000 minioadmin minioadmin`
  - `mc mb myminio/cfdi-zip`

Test rapido R2:
```
$env:SAT_STORAGE_BACKEND = "r2"
$env:R2_ENDPOINT = "http://127.0.0.1:9000"
$env:R2_ACCESS_KEY = "minioadmin"
$env:R2_SECRET_KEY = "minioadmin"
$env:R2_BUCKET = "cfdi-zip"
$env:R2_REGION = "auto"
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -vv tests/integration/test_storage_r2.py
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
- Auth: `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
- Usuarios: `GET /users`, `POST /users`, `PUT /users/{id}`, `DELETE /users/{id}`.
