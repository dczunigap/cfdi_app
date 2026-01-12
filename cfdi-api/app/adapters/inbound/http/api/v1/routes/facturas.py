from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.adapters.inbound.http.api.v1.schemas.facturas import (
    ConceptoResponse,
    FacturaDetailResponse,
    FacturaListResponse,
    PagoResponse,
)
from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.db.repositories.facturas import SqlFacturaRepository
from app.adapters.outbound.db.repositories.conceptos import SqlConceptoRepository
from app.adapters.outbound.db.repositories.pagos import SqlPagoRepository
from app.application.facturas.use_cases import (
    GetFacturaDetailInput,
    GetFacturaDetailUseCase,
    ListFacturasInput,
    ListFacturasUseCase,
)

router = APIRouter(prefix="/facturas", tags=["facturas"])


@router.get(
    "/",
    response_model=list[FacturaListResponse],
    summary="Lista facturas",
    description="Devuelve facturas filtradas por year, month, tipo y naturaleza.",
)
def listar_facturas(
    year: Optional[int] = None,
    month: Optional[int] = None,
    tipo: Optional[str] = None,
    naturaleza: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[FacturaListResponse]:
    repo = SqlFacturaRepository(db)
    use_case = ListFacturasUseCase(repo)
    data = ListFacturasInput(year=year, month=month, tipo=tipo, naturaleza=naturaleza)
    items = use_case.execute(data)
    return [FacturaListResponse(**item.__dict__) for item in items]


@router.get(
    "/{factura_id}",
    response_model=FacturaDetailResponse,
    summary="Detalle de factura",
    description="Devuelve factura con sus conceptos y pagos.",
)
def detalle_factura(factura_id: int, db: Session = Depends(get_db)) -> FacturaDetailResponse:
    factura_repo = SqlFacturaRepository(db)
    concepto_repo = SqlConceptoRepository(db)
    pago_repo = SqlPagoRepository(db)
    use_case = GetFacturaDetailUseCase(factura_repo, concepto_repo, pago_repo)
    result = use_case.execute(GetFacturaDetailInput(factura_id=factura_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    return FacturaDetailResponse(
        factura=FacturaListResponse(**result.factura.__dict__),
        conceptos=[ConceptoResponse(**c.__dict__) for c in result.conceptos],
        pagos=[PagoResponse(**p.__dict__) for p in result.pagos],
    )
