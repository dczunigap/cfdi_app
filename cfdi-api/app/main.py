from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.outbound.db.session import Base, engine
from app.adapters.outbound.db import models  # noqa: F401
from app.adapters.inbound.http.api.v1.routes import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="CFDI API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:4200",
            "http://127.0.0.1:4200",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.on_event("startup")
    def init_db() -> None:
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
