from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db, require_user
from app.adapters.inbound.http.api.v1.schemas.user_rfcs import (
    UserRfcCreateRequest,
    UserRfcResponse,
)
from app.adapters.outbound.db.repositories.user_rfcs import SqlUserRfcsRepository
from app.adapters.outbound.db.repositories.users import SqlUserRepository

router = APIRouter(prefix="/user-rfcs", tags=["user-rfcs"], dependencies=[Depends(require_user)])


def _normalize_rfc(value: str | None) -> str:
    rfc = (value or "").strip().upper()
    if not rfc or not re.match(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$", rfc):
        raise HTTPException(status_code=400, detail="RFC invalido")
    return rfc


def _ensure_user(db: Session, user_id: int):
    users = SqlUserRepository(db)
    user = users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get("", response_model=list[UserRfcResponse])
def list_user_rfcs(
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
) -> list[UserRfcResponse]:
    _ensure_user(db, user_id)
    repo = SqlUserRfcsRepository(db)
    rfcs = repo.list_by_user(user_id)
    return [UserRfcResponse(user_id=user_id, rfc=rfc) for rfc in rfcs]


@router.post("", response_model=UserRfcResponse)
def add_user_rfc(
    payload: UserRfcCreateRequest,
    db: Session = Depends(get_db),
) -> UserRfcResponse:
    user_id = payload.user_id
    _ensure_user(db, user_id)
    rfc = _normalize_rfc(payload.rfc)
    repo = SqlUserRfcsRepository(db)
    if repo.is_allowed(user_id, rfc):
        raise HTTPException(status_code=409, detail="RFC ya asociado al usuario")
    repo.add(user_id, rfc)
    return UserRfcResponse(user_id=user_id, rfc=rfc)


@router.delete("/{user_id}/{rfc}")
def remove_user_rfc(
    user_id: int,
    rfc: str,
    db: Session = Depends(get_db),
) -> dict:
    _ensure_user(db, user_id)
    rfc_value = _normalize_rfc(rfc)
    repo = SqlUserRfcsRepository(db)
    if not repo.is_allowed(user_id, rfc_value):
        raise HTTPException(status_code=404, detail="Relacion no encontrada")
    repo.remove(user_id, rfc_value)
    return {"ok": True}
