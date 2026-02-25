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
from app.adapters.outbound.db.repositories.users import SqlUserRepository
from app.core.config import settings
from app.core.security import hash_password


def _build_client(seed_user: bool = True) -> TestClient:
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    if seed_user:
        with SessionLocal() as db:
            repo = SqlUserRepository(db)
            repo.create(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("demo123", settings.auth_password_iterations),
            )

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
    settings.auth_refresh_secret = "test-refresh-secret"
    settings.auth_token_ttl_minutes = 60
    settings.auth_refresh_ttl_days = 7
    settings.auth_password_iterations = 1000


def test_auth_bootstrap_login_me_logout() -> None:
    _set_test_settings()
    client = _build_client()

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


def test_auth_login_invalid_credentials() -> None:
    _set_test_settings()
    client = _build_client()

    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "bad"})
    assert res.status_code == 401


def test_auth_refresh_and_token_status() -> None:
    _set_test_settings()
    client = _build_client()

    login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "demo123"})
    assert login.status_code == 200
    payload = login.json()
    access_token = payload["access_token"]
    refresh_token = payload["refresh_token"]

    status_res = client.get("/api/v1/auth/token-status", headers={"Authorization": f"Bearer {access_token}"})
    assert status_res.status_code == 200
    status_payload = status_res.json()
    assert status_payload["active"] is True
    assert status_payload["token_type"] == "access"

    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refreshed = refresh_res.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]
