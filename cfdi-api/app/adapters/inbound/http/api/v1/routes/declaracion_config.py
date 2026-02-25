from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db, require_admin
from app.adapters.inbound.http.api.v1.schemas.declaracion_config import (
    DeclaracionConfigCatalogsResponse,
    DeclaracionConfigGetResponse,
    DeclaracionConfigUpsertRequest,
    DeclaracionConfigUpsertResponse,
)
from app.adapters.outbound.db.repositories.declaracion_config import SqlDeclaracionConfigRepository

router = APIRouter(
    prefix="/admin/declaracion-config",
    tags=["admin-declaracion-config"],
    dependencies=[Depends(require_admin)],
)


@router.get("/catalogos", response_model=DeclaracionConfigCatalogsResponse)
def list_catalogos(db: Session = Depends(get_db)) -> DeclaracionConfigCatalogsResponse:
    repo = SqlDeclaracionConfigRepository(db)
    payload = repo.list_catalogs()
    return DeclaracionConfigCatalogsResponse(**payload)


@router.get("", response_model=DeclaracionConfigGetResponse)
def get_config(
    regimen_fiscal_clave: str = Query(..., min_length=3),
    tipo_declaracion: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
) -> DeclaracionConfigGetResponse:
    repo = SqlDeclaracionConfigRepository(db)
    config = repo.get_config(
        regimen_fiscal_clave=(regimen_fiscal_clave or "").strip().upper(),
        tipo_declaracion_clave=(tipo_declaracion or "").strip().upper(),
    )
    if not config:
        raise HTTPException(status_code=404, detail="Configuracion no encontrada")
    return DeclaracionConfigGetResponse(**config)


@router.put("", response_model=DeclaracionConfigUpsertResponse)
def upsert_config(
    payload: DeclaracionConfigUpsertRequest,
    db: Session = Depends(get_db),
) -> DeclaracionConfigUpsertResponse:
    repo = SqlDeclaracionConfigRepository(db)
    try:
        config_id = repo.upsert_config(
            regimen_fiscal_clave=(payload.regimen_fiscal_clave or "").strip().upper(),
            tipo_declaracion_clave=(payload.tipo_declaracion_clave or "").strip().upper(),
            activo=payload.activo,
            incluir_acumulado_mensual_en_anual=payload.incluir_acumulado_mensual_en_anual,
            usos_cfdi=[item.model_dump() for item in payload.usos_cfdi],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DeclaracionConfigUpsertResponse(ok=True, config_id=config_id)
