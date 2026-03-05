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
    settings.auth_refresh_secret = "test-refresh-secret"
    settings.auth_token_ttl_minutes = 60
    settings.auth_refresh_ttl_days = 7
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
        _seed_declaracion_config(db)
        _seed_facturas(db)
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


def _seed_declaracion_config(db) -> None:
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
    db.add(TipoDeclaracionCatalogModel(clave="ANUAL", descripcion="Anual", activo=True))
    db.add(UsoCfdiDeduccionCatalogModel(clave="G03", descripcion="Gastos en general", tipo_declaracion_clave="MENSUAL", activo=True))
    db.add(UsoCfdiDeduccionCatalogModel(clave="D01", descripcion="Honorarios medicos", tipo_declaracion_clave="ANUAL", activo=True))
    db.flush()

    config_mensual = RegimenDeclaracionConfigModel(
        regimen_fiscal_id=regimen.id,
        tipo_declaracion_clave="MENSUAL",
        activo=True,
    )
    db.add(config_mensual)
    db.flush()
    db.add(
        RegimenDeclaracionConfigDetalleModel(
            config_id=config_mensual.id,
            uso_cfdi_clave="G03",
            orden=1,
        )
    )

    config_anual = RegimenDeclaracionConfigModel(
        regimen_fiscal_id=regimen.id,
        tipo_declaracion_clave="ANUAL",
        activo=True,
    )
    db.add(config_anual)
    db.flush()
    db.add(
        RegimenDeclaracionConfigDetalleModel(
            config_id=config_anual.id,
            uso_cfdi_clave="D01",
            orden=1,
        )
    )


def _seed_facturas(db) -> None:
    db.add(
        FacturaModel(
            uuid="uuid-deducible",
            tipo_comprobante="I",
            fecha_emision=datetime(2025, 7, 10),
            year_emision=2025,
            month_emision=7,
            naturaleza="gasto",
            emisor_rfc="XEXX010101000",
            receptor_rfc=TEST_RFC,
            uso_cfdi="G03",
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
            uuid="uuid-no-deducible",
            tipo_comprobante="I",
            fecha_emision=datetime(2025, 7, 11),
            year_emision=2025,
            month_emision=7,
            naturaleza="gasto",
            emisor_rfc="XEXX010101000",
            receptor_rfc=TEST_RFC,
            uso_cfdi="P01",
            subtotal=200.0,
            descuento=0.0,
            total=232.0,
            total_trasladados=32.0,
            total_retenidos=0.0,
            moneda="MXN",
            xml_text="<xml/>",
        )
    )
    db.add(
        FacturaModel(
            uuid="uuid-no-deducible-sin-uso",
            tipo_comprobante="I",
            fecha_emision=datetime(2025, 7, 12),
            year_emision=2025,
            month_emision=7,
            naturaleza="gasto",
            emisor_rfc="XEXX010101000",
            receptor_rfc=TEST_RFC,
            uso_cfdi=None,
            subtotal=300.0,
            descuento=0.0,
            total=348.0,
            total_trasladados=48.0,
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


def test_deducciones_catalogo_returns_expected_payload() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get("/api/v1/deducciones/catalogo?tipo_declaracion=MENSUAL", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["rfc"] == TEST_RFC
    assert payload["tipo_declaracion"] == "MENSUAL"
    assert payload["regimen_fiscal"]["clave"] == "626"
    assert payload["usos_cfdi"] == [{"clave": "G03", "descripcion": "Gastos en general", "orden": 1}]
    assert "incluir_acumulado_mensual_en_anual" not in payload


def test_facturas_filter_deducibles() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get(
        "/api/v1/facturas/?year=2025&month=7&deducibilidad=DEDUCIBLES&tipo_declaracion=MENSUAL",
        headers=headers,
    )
    assert res.status_code == 200
    payload = res.json()
    assert [item["uuid"] for item in payload] == ["uuid-deducible"]


def test_facturas_filter_no_deducibles() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get(
        "/api/v1/facturas/?year=2025&month=7&deducibilidad=NO_DEDUCIBLES&tipo_declaracion=MENSUAL",
        headers=headers,
    )
    assert res.status_code == 200
    payload = res.json()
    assert {item["uuid"] for item in payload} == {"uuid-no-deducible", "uuid-no-deducible-sin-uso"}


def test_facturas_filter_invalid_deducibilidad() -> None:
    _set_test_settings()
    client = _build_client()
    headers = _auth_headers(client)

    res = client.get("/api/v1/facturas/?deducibilidad=INVALIDA", headers=headers)
    assert res.status_code == 400
    assert "deducibilidad invalida" in res.json()["detail"]
