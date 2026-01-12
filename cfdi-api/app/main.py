from fastapi import FastAPI
from app.adapters.inbound.http.api.v1.routes import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="CFDI API")
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
