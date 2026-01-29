from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.schemas.auth import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    AuthUserResponse,
)
from app.adapters.inbound.http.deps import get_db, optional_user, require_user
from app.adapters.outbound.db.repositories.users import SqlUserRepository
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalize_username(username: str) -> str:
    return (username or "").strip()


@router.post("/register", response_model=AuthUserResponse, summary="Registro de usuario")
def register_user(
    payload: AuthRegisterRequest,
    db: Session = Depends(get_db),
    current_user=Depends(optional_user),
) -> AuthUserResponse:
    username = _normalize_username(payload.username)
    email = _normalize_email(payload.email)
    password = (payload.password or "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username requerido")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Correo invalido")
    if not password:
        raise HTTPException(status_code=400, detail="Password requerido")

    repo = SqlUserRepository(db)
    if current_user is None and repo.count_users() > 0:
        raise HTTPException(status_code=401, detail="No autorizado")
    if repo.get_by_username(username.lower()):
        raise HTTPException(status_code=409, detail="Username ya registrado")
    if repo.get_by_email(email):
        raise HTTPException(status_code=409, detail="Correo ya registrado")

    password_hash = hash_password(password, settings.auth_password_iterations)
    user = repo.create(username=username, email=email, password_hash=password_hash)
    return AuthUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
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

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        username=user.username,
        secret=settings.auth_secret,
        ttl_minutes=settings.auth_token_ttl_minutes,
    )
    repo.update_last_login(user)
    return AuthTokenResponse(
        access_token=token,
        expires_in=int(settings.auth_token_ttl_minutes) * 60,
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
