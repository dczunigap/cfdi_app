from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db
from app.adapters.inbound.http.api.v1.schemas.platform_rfcs import (
    PlatformRfcCreateRequest,
    PlatformRfcResponse,
)
from app.adapters.outbound.db.repositories.platform_rfcs import SqlPlatformRfcRepository

router = APIRouter(prefix="/platform-rfcs", tags=["platform-rfcs"])


def _normalize_rfc(value: str | None) -> str:
    return (value or "").strip().upper()


@router.get("", response_model=list[PlatformRfcResponse])
def list_platform_rfcs(db: Session = Depends(get_db)) -> list[PlatformRfcResponse]:
    repo = SqlPlatformRfcRepository(db)
    items = repo.list_all()
    return [PlatformRfcResponse(id=i.id, rfc=i.rfc, nombre=i.nombre) for i in items]


@router.post("", response_model=PlatformRfcResponse)
def add_platform_rfc(
    payload: PlatformRfcCreateRequest, db: Session = Depends(get_db)
) -> PlatformRfcResponse:
    repo = SqlPlatformRfcRepository(db)
    rfc = _normalize_rfc(payload.rfc)
    if not rfc:
        raise HTTPException(status_code=400, detail="RFC requerido")
    existing = repo.get_by_rfc(rfc)
    if existing:
        return PlatformRfcResponse(id=existing.id, rfc=existing.rfc, nombre=existing.nombre)
    model = repo.add(rfc=rfc, nombre=(payload.nombre or "").strip() or None)
    return PlatformRfcResponse(id=model.id, rfc=model.rfc, nombre=model.nombre)


@router.delete("/{rfc_id}")
def delete_platform_rfc(rfc_id: int, db: Session = Depends(get_db)) -> dict:
    repo = SqlPlatformRfcRepository(db)
    model = repo.get_by_id(rfc_id)
    if not model:
        raise HTTPException(status_code=404, detail="RFC no encontrado")
    repo.delete(model)
    return {"ok": True}
