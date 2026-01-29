from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.schemas.users import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.repositories.users import SqlUserRepository
from app.core.config import settings
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _to_response(model) -> UserResponse:
    return UserResponse(
        id=model.id,
        username=model.username,
        email=model.email,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
        last_login_at=model.last_login_at,
    )


@router.get("", response_model=list[UserResponse], summary="Listado de usuarios")
def list_users(
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    repo = SqlUserRepository(db)
    users = repo.list_all()
    return [_to_response(user) for user in users]


@router.post("", response_model=UserResponse, summary="Crear usuario")
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
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
    if repo.get_by_username(username):
        raise HTTPException(status_code=409, detail="Username ya registrado")
    if repo.get_by_email(email):
        raise HTTPException(status_code=409, detail="Correo ya registrado")

    password_hash = hash_password(password, settings.auth_password_iterations)
    user = repo.create(username=username, email=email, password_hash=password_hash)
    if payload.is_active is not None and user.is_active != payload.is_active:
        user.is_active = payload.is_active
        user = repo.update(user)

    return _to_response(user)


@router.put("/{user_id}", response_model=UserResponse, summary="Actualizar usuario")
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    repo = SqlUserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.username is not None:
        username = _normalize_username(payload.username)
        if not username:
            raise HTTPException(status_code=400, detail="Username requerido")
        existing = repo.get_by_username(username)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=409, detail="Username ya registrado")
        user.username = username

    if payload.email is not None:
        email = _normalize_email(payload.email)
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Correo invalido")
        existing = repo.get_by_email(email)
        if existing and existing.id != user.id:
            raise HTTPException(status_code=409, detail="Correo ya registrado")
        user.email = email

    if payload.password is not None:
        password = (payload.password or "").strip()
        if not password:
            raise HTTPException(status_code=400, detail="Password requerido")
        user.password_hash = hash_password(password, settings.auth_password_iterations)

    if payload.is_active is not None:
        user.is_active = payload.is_active

    user = repo.update(user)
    return _to_response(user)


@router.delete("/{user_id}", summary="Eliminar usuario")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> dict:
    repo = SqlUserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    repo.delete(user)
    return {"ok": True}
