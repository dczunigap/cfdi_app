# cfdi-api
Backend Python (FastAPI) con arquitectura hexagonal ligera.

## Requisitos
- Python 3.10+

## Variables de entorno
- `CFDI_DB_URL` (default: `sqlite:///./data/contabilidad.sqlite`)

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

## Estructura
- `app/domain`: entidades y reglas puras
- `app/application`: casos de uso y DTOs
- `app/ports`: interfaces de salida
- `app/adapters`: inbound (HTTP) y outbound (DB/files)

## API
- Base: `/api/v1`
- OpenAPI: `GET /openapi.json`
