from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db, require_user
from app.adapters.inbound.http.api.v1.schemas.rfc_phones import (
    RfcPhoneCreateRequest,
    RfcPhoneResponse,
)
from app.adapters.outbound.db.repositories.rfc_phones import SqlRfcPhoneRepository

router = APIRouter(prefix="/rfc-phones", tags=["rfc-phones"], dependencies=[Depends(require_user)])


def _normalize_phone(value: str | None) -> str:
    digits = re.sub(r"\D+", "", value or "")
    if not digits or len(digits) < 8 or len(digits) > 15:
        raise HTTPException(status_code=400, detail="Telefono invalido")
    return digits


def _normalize_rfc(value: str | None) -> str:
    rfc = (value or "").strip().upper()
    if not rfc or not re.match(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$", rfc):
        raise HTTPException(status_code=400, detail="RFC invalido")
    return rfc


@router.get("", response_model=list[RfcPhoneResponse])
def list_rfc_phones(db: Session = Depends(get_db)) -> list[RfcPhoneResponse]:
    repo = SqlRfcPhoneRepository(db)
    items = repo.list_all()
    return [RfcPhoneResponse(id=i.id, phone=i.phone, rfc=i.rfc) for i in items]


@router.get("/resolve", response_model=RfcPhoneResponse)
def resolve_rfc_phone(phone: str, db: Session = Depends(get_db)) -> RfcPhoneResponse:
    repo = SqlRfcPhoneRepository(db)
    normalized = _normalize_phone(phone)
    item = repo.get_by_phone(normalized)
    if not item:
        raise HTTPException(status_code=404, detail="Telefono no registrado")
    return RfcPhoneResponse(id=item.id, phone=item.phone, rfc=item.rfc)


@router.post("", response_model=RfcPhoneResponse)
def upsert_rfc_phone(
    payload: RfcPhoneCreateRequest, db: Session = Depends(get_db)
) -> RfcPhoneResponse:
    repo = SqlRfcPhoneRepository(db)
    phone = _normalize_phone(payload.phone)
    rfc = _normalize_rfc(payload.rfc)
    model = repo.upsert(phone=phone, rfc=rfc)
    return RfcPhoneResponse(id=model.id, phone=model.phone, rfc=model.rfc)


@router.delete("/{phone_id}")
def delete_rfc_phone(phone_id: int, db: Session = Depends(get_db)) -> dict:
    repo = SqlRfcPhoneRepository(db)
    model = repo.get_by_id(phone_id)
    if not model:
        raise HTTPException(status_code=404, detail="Telefono no encontrado")
    repo.delete(model)
    return {"ok": True}
