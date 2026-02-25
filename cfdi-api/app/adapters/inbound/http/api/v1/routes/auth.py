from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.schemas.auth import (
    AuthLoginRequest,
    AuthRefreshRequest,
    AuthTokenResponse,
    AuthTokenStatusResponse,
    AuthUserResponse,
)
from app.adapters.inbound.http.deps import get_db, require_user
from app.adapters.outbound.db.repositories.users import SqlUserRepository
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    decode_signed_token,
    is_token_expired,
    parse_bearer_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalize_username(username: str) -> str:
    return (username or "").strip()


def _issue_tokens(user) -> AuthTokenResponse:
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        secret=settings.auth_secret,
        ttl_minutes=settings.auth_token_ttl_minutes,
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        secret=settings.auth_refresh_secret,
        ttl_days=settings.auth_refresh_ttl_days,
    )
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(settings.auth_token_ttl_minutes) * 60,
        refresh_expires_in=int(settings.auth_refresh_ttl_days) * 24 * 60 * 60,
    )


@router.post("/login", response_model=AuthTokenResponse, summary="Login")
def login_user(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    email = _normalize_email(payload.email)
    password = payload.password or ""
    repo = SqlUserRepository(db)
    user = repo.get_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    repo.update_last_login(user)
    return _issue_tokens(user)


@router.post("/refresh", response_model=AuthTokenResponse, summary="Refresh token")
def refresh_token(payload: AuthRefreshRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    refresh_payload = decode_refresh_token(payload.refresh_token, settings.auth_refresh_secret)
    if not refresh_payload:
        raise HTTPException(status_code=401, detail="Refresh token invalido o expirado")
    user_id = refresh_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    repo = SqlUserRepository(db)
    user = repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no autorizado")
    return _issue_tokens(user)


@router.get("/token-status", response_model=AuthTokenStatusResponse, summary="Estado del token")
def token_status(authorization: str | None = Header(default=None, alias="Authorization")) -> AuthTokenStatusResponse:
    token = parse_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token requerido")

    payload = decode_signed_token(token, settings.auth_secret)
    token_type = "access"
    if not payload:
        payload = decode_signed_token(token, settings.auth_refresh_secret)
        token_type = "refresh"
    if not payload:
        return AuthTokenStatusResponse(
            active=False,
            expired=True,
            token_type=None,
            user_id=None,
            email=None,
            username=None,
            expires_at=None,
            seconds_left=None,
        )

    exp = payload.get("exp")
    now = int(time.time())
    seconds_left = None if exp is None else max(0, int(exp) - now)
    expired = is_token_expired(payload)
    if payload.get("typ") == "refresh":
        token_type = "refresh"

    user_id_raw = payload.get("sub")
    return AuthTokenStatusResponse(
        active=not expired,
        expired=expired,
        token_type=token_type,
        user_id=int(user_id_raw) if str(user_id_raw or "").isdigit() else None,
        email=payload.get("email"),
        username=payload.get("username"),
        expires_at=int(exp) if exp is not None else None,
        seconds_left=seconds_left,
    )


@router.post("/logout", summary="Logout")
def logout_user(_user=Depends(require_user)) -> dict:
    return {"ok": True}


@router.get("/me", response_model=AuthUserResponse, summary="Usuario actual")
def me(user=Depends(require_user)) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
