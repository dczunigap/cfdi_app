from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.schemas.retenciones import (
    RetencionDetailResponse,
    RetencionListResponse,
)
from app.adapters.outbound.db.repositories.retenciones import SqlRetencionRepository
from app.adapters.inbound.http.deps import get_db
from app.application.retenciones.use_cases import (
    GetRetencionDetailInput,
    GetRetencionDetailUseCase,
    ListRetencionesInput,
    ListRetencionesUseCase,
)

router = APIRouter(prefix="/retenciones", tags=["retenciones"])


@router.get(
    "/",
    response_model=list[RetencionListResponse],
    summary="Lista retenciones",
    description="Devuelve retenciones filtradas por year y month.",
)
def listar_retenciones(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
) -> list[RetencionListResponse]:
    repo = SqlRetencionRepository(db)
    use_case = ListRetencionesUseCase(repo)
    data = ListRetencionesInput(year=year, month=month)
    items = use_case.execute(data)
    return [RetencionListResponse(**item.__dict__) for item in items]


@router.get(
    "/{retencion_id}",
    response_model=RetencionDetailResponse,
    summary="Detalle de retencion",
    description="Devuelve el detalle de una retencion de plataformas.",
)
def detalle_retencion(
    retencion_id: int,
    db: Session = Depends(get_db),
) -> RetencionDetailResponse:
    repo = SqlRetencionRepository(db)
    use_case = GetRetencionDetailUseCase(repo)
    result = use_case.execute(GetRetencionDetailInput(retencion_id=retencion_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Retencion no encontrada")
    return RetencionDetailResponse(**result.__dict__)
