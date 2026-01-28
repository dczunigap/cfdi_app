from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.inbound.http.api.v1.routes import api_router
from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.session import Base
from app.adapters.outbound.db import models  # noqa: F401
from app.core.config import settings


def _build_client() -> TestClient:
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

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def _set_test_settings() -> None:
    settings.auth_secret = "test-secret"
    settings.auth_token_ttl_minutes = 60
    settings.auth_password_iterations = 1000


def test_auth_bootstrap_login_me_logout() -> None:
    _set_test_settings()
    client = _build_client()

    payload = {"username": "admin", "email": "admin@example.com", "password": "demo123"}
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 200
    assert res.json()["username"] == "admin"

    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "demo123"})
    assert res.status_code == 200
    token = res.json()["access_token"]

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "admin@example.com"

    res = client.post("/api/v1/auth/logout")
    assert res.status_code == 401

    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_auth_register_requires_auth_after_bootstrap() -> None:
    _set_test_settings()
    client = _build_client()

    res = client.post(
        "/api/v1/auth/register",
        json={"username": "admin", "email": "admin@example.com", "password": "demo123"},
    )
    assert res.status_code == 200

    res = client.post(
        "/api/v1/auth/register",
        json={"username": "user2", "email": "user2@example.com", "password": "demo123"},
    )
    assert res.status_code == 401


def test_auth_login_invalid_credentials() -> None:
    _set_test_settings()
    client = _build_client()

    res = client.post(
        "/api/v1/auth/register",
        json={"username": "admin", "email": "admin@example.com", "password": "demo123"},
    )
    assert res.status_code == 200

    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "bad"})
    assert res.status_code == 401


def test_guard_blocks_without_token() -> None:
    _set_test_settings()
    client = _build_client()

    res = client.get("/api/v1/facturas")
    assert res.status_code == 401

    res = client.post(
        "/api/v1/auth/register",
        json={"username": "admin", "email": "admin@example.com", "password": "demo123"},
    )
    assert res.status_code == 200
    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "demo123"})
    token = res.json()["access_token"]

    res = client.get("/api/v1/facturas", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
