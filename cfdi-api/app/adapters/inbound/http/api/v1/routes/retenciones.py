from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.schemas.retenciones import (
    RetencionDetailResponse,
    RetencionListResponse,
)
from app.adapters.inbound.http.api.v1.mappers import (
    retencion_detail_to_dto,
    retencion_list_to_dto,
)
from app.adapters.outbound.db.repositories.retenciones import SqlRetencionRepository
from app.adapters.inbound.http.deps import get_db, get_required_rfc, require_user
from app.adapters.outbound.db.models import RetencionModel
from app.adapters.inbound.http.api.v1.routes.utils import get_or_404
from app.application.retenciones.use_cases import (
    GetRetencionDetailInput,
    GetRetencionDetailUseCase,
    ListRetencionesInput,
    ListRetencionesUseCase,
)

router = APIRouter(prefix="/retenciones", tags=["retenciones"], dependencies=[Depends(require_user)])


@router.get(
    "/",
    response_model=list[RetencionListResponse],
    summary="Lista retenciones",
    description="Devuelve retenciones filtradas por year y month.",
)
def listar_retenciones(
    year: Optional[int] = None,
    month: Optional[int] = None,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> list[RetencionListResponse]:
    repo = SqlRetencionRepository(db)
    use_case = ListRetencionesUseCase(repo)
    data = ListRetencionesInput(year=year, month=month, rfc=x_rfc)
    items = use_case.execute(data)
    return retencion_list_to_dto(items)


@router.get(
    "/{retencion_id}",
    response_model=RetencionDetailResponse,
    summary="Detalle de retencion",
    description="Devuelve el detalle de una retencion de plataformas.",
)
def detalle_retencion(
    retencion_id: int,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> RetencionDetailResponse:
    repo = SqlRetencionRepository(db)
    use_case = GetRetencionDetailUseCase(repo)
    result = use_case.execute(GetRetencionDetailInput(retencion_id=retencion_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Retencion no encontrada")
    if result.emisor_rfc != x_rfc and result.receptor_rfc != x_rfc:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return retencion_detail_to_dto(result)


@router.delete(
    "/{retencion_id}",
    summary="Eliminar retencion",
    description="Elimina una retencion por ID.",
)
def eliminar_retencion(
    retencion_id: int,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> dict:
    row = get_or_404(db, RetencionModel, retencion_id, "Retencion")
    if row.emisor_rfc != x_rfc and row.receptor_rfc != x_rfc:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    db.delete(row)
    db.commit()
    return {"ok": True}
