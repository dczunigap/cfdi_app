from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.inbound.http.api.v1.routes import api_router
from app.adapters.inbound.http.deps import get_db, require_user
from app.adapters.outbound.db.session import Base
from app.adapters.outbound.db import models  # noqa: F401
from app.domain.sat.entities import SatDescarga
from app.adapters.outbound.db.repositories.user_rfcs import SqlUserRfcsRepository


def _build_client(allow_rfc: bool = True) -> TestClient:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    def _override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _override_user():
        return type("User", (), {"id": 1})()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[require_user] = _override_user

    if allow_rfc:
        with SessionLocal() as db:
            repo = SqlUserRfcsRepository(db)
            repo.add(user_id=1, rfc="AAA010101AAA")
    return TestClient(app)


def test_create_descarga_basica(monkeypatch) -> None:
    client = _build_client()

    fake = SatDescarga(
        id=1,
        rfc="AAA010101AAA",
        kind="cfdi",
        tipo_solicitud="emitidos",
        anio_filtro=2024,
        mes_filtro=1,
        id_solicitud="SAT-123",
        estado="SOLICITADA",
        paquetes=[],
        link_descarga=None,
        zip_path=None,
        attempts=0,
        next_check_at=datetime.now(timezone.utc),
        last_error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )

    from app.adapters.inbound.http.api.v1.routes import sat_descargas as routes

    monkeypatch.setattr(routes, "crear_solicitud_descarga", lambda **kwargs: fake)
    monkeypatch.setattr(routes, "verificar_descarga_job", lambda *args, **kwargs: None, raising=False)

    res = client.post(
        "/api/v1/sat/descargas",
        headers={"X-RFC": "AAA010101AAA"},
        json={
            "kind": "cfdi",
            "tipo_solicitud": "emitidos",
            "fecha_inicial": "2024-01-01T00:00:00Z",
            "fecha_final": "2024-01-31T23:59:59Z",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == 1
    assert body["rfc"] == "AAA010101AAA"
    assert body["estado"] == "SOLICITADA"


def test_create_descarga_forbidden_without_permission(monkeypatch) -> None:
    client = _build_client(allow_rfc=False)

    from app.adapters.inbound.http.api.v1.routes import sat_descargas as routes

    monkeypatch.setattr(routes, "crear_solicitud_descarga", lambda **kwargs: None)
    monkeypatch.setattr(routes, "verificar_descarga_job", lambda *args, **kwargs: None, raising=False)

    res = client.post(
        "/api/v1/sat/descargas",
        headers={"X-RFC": "AAA010101AAA"},
        json={
            "kind": "cfdi",
            "tipo_solicitud": "emitidos",
            "fecha_inicial": "2024-01-01T00:00:00Z",
            "fecha_final": "2024-01-31T23:59:59Z",
        },
    )

    assert res.status_code == 403
