from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.inbound.http.api.v1.routes import api_router
from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db import models  # noqa: F401
from app.adapters.outbound.db.models import (
    FacturaModel,
    RegimenDeclaracionConfigDetalleModel,
    RegimenDeclaracionConfigModel,
    RegimenFiscalCatalogModel,
    RfcModel,
    TipoDeclaracionCatalogModel,
    TipoPersonaCatalogModel,
    UsoCfdiDeduccionCatalogModel,
)
from app.adapters.outbound.db.repositories.users import SqlUserRepository
from app.adapters.outbound.db.session import Base
from app.core.config import settings
from app.core.security import hash_password


TEST_RFC = "AAA010101AAA"


def _set_test_settings() -> None:
    settings.auth_secret = "test-secret"
    settings.auth_token_ttl_minutes = 60
    settings.auth_password_iterations = 1000


def _build_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as db:
        repo = SqlUserRepository(db)
        repo.create(
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("demo123", settings.auth_password_iterations),
        )
        _seed_reportes_config(db)
        _seed_reportes_data(db)
        db.commit()

    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    def _override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def _seed_reportes_config(db) -> None:
    db.add(TipoPersonaCatalogModel(clave="PM", descripcion="Persona moral"))
    db.flush()
    regimen = RegimenFiscalCatalogModel(
        tipo_persona_clave="PM",
        clave="626",
        descripcion="RESICO PM",
        activo=True,
    )
    db.add(regimen)
    db.flush()

    db.add(RfcModel(rfc=TEST_RFC, regimen_fiscal_id=regimen.id))

    db.add(TipoDeclaracionCatalogModel(clave="MENSUAL", descripcion="Mensual", activo=True))
    db.add(UsoCfdiDeduccionCatalogModel(clave="G03", descripcion="Gastos en general", tipo_declaracion_clave="MENSUAL", activo=True))
    db.flush()

    config = RegimenDeclaracionConfigModel(
        regimen_fiscal_id=regimen.id,
        tipo_declaracion_clave="MENSUAL",
        activo=True,
    )
    db.add(config)
    db.flush()

    db.add(
        RegimenDeclaracionConfigDetalleModel(
            config_id=config.id,
            uso_cfdi_clave="G03",
            orden=1,
        )
    )


def _seed_reportes_data(db) -> None:
    db.add(
        FacturaModel(
            uuid="uuid-ingreso-1",
            tipo_comprobante="I",
            fecha_emision=datetime(2025, 7, 10),
            year_emision=2025,
            month_emision=7,
            naturaleza="ingreso",
            emisor_rfc=TEST_RFC,
            receptor_rfc="XAXX010101000",
            uso_cfdi="P01",
            subtotal=100.0,
            descuento=0.0,
            total=116.0,
            total_trasladados=16.0,
            total_retenidos=0.0,
            moneda="MXN",
            xml_text="<xml/>",
        )
    )
    db.add(
        FacturaModel(
            uuid="uuid-gasto-1",
            tipo_comprobante="I",
            fecha_emision=datetime(2025, 7, 11),
            year_emision=2025,
            month_emision=7,
            naturaleza="gasto",
            emisor_rfc="XEXX010101000",
            receptor_rfc=TEST_RFC,
            uso_cfdi="G03",
            subtotal=50.0,
            descuento=0.0,
            total=58.0,
            total_trasladados=8.0,
            total_retenidos=0.0,
            moneda="MXN",
            xml_text="<xml/>",
        )
    )


def _auth_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "demo123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-RFC": TEST_RFC,
    }


def test_summary_endpoint_monthly() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get("/api/v1/summary?year=2025&month=7&tipo_declaracion=MENSUAL", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["year"] == 2025
    assert payload["month"] == 7
    assert payload["mi_rfc"] == TEST_RFC
    assert payload["ingresos_total"] > 0


def test_summary_details_endpoint_monthly() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get("/api/v1/summary/details?year=2025&month=7&tipo_declaracion=MENSUAL", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["tipo_declaracion"] == "MENSUAL"
    assert payload["year"] == 2025
    assert payload["month"] == 7
    assert isinstance(payload["docs"], list)
    assert isinstance(payload["pagos"], list)


def test_declaracion_endpoint_monthly() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get(
        "/api/v1/declaracion?year=2025&month=7&tipo_declaracion=MENSUAL&income_source=cfdi",
        headers=headers,
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["year"] == 2025
    assert payload["month"] == 7
    assert payload["mi_rfc"] == TEST_RFC
    assert "checks" in payload


def test_sat_report_csv_endpoint() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get("/api/v1/sat_report.csv?year=2025&month=7&income_source=cfdi", headers=headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert "periodo" in res.text
    assert "2025-07" in res.text


def test_sat_hoja_txt_endpoint() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get("/api/v1/sat_hoja.txt?year=2025&month=7&income_source=cfdi", headers=headers)
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    assert "PERIODO: 2025-07" in res.text
