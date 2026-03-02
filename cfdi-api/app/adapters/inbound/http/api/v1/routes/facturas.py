from __future__ import annotations

from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import HTTPException
from starlette.responses import Response

from app.adapters.inbound.http.api.v1.schemas.facturas import (
    FacturaDetailResponse,
    FacturaListResponse,
)
from app.adapters.inbound.http.api.v1.mappers import (
    factura_detail_to_dto,
    factura_list_to_dto,
)
from app.adapters.inbound.http.deps import get_db, get_required_rfc, require_user
from app.adapters.outbound.db.repositories.facturas import SqlFacturaRepository
from app.adapters.inbound.http.api.v1.routes.utils import csv_response, xml_response
from app.adapters.outbound.db.repositories.conceptos import SqlConceptoRepository
from app.adapters.outbound.db.repositories.pagos import SqlPagoRepository
from app.application.facturas.use_cases import (
    DeleteFacturaInput,
    DeleteFacturaUseCase,
    GetFacturaXmlInput,
    GetFacturaXmlUseCase,
    GetFacturaDetailInput,
    GetFacturaDetailUseCase,
    ListFacturasInput,
    ListFacturasUseCase,
)

router = APIRouter(prefix="/facturas", tags=["facturas"], dependencies=[Depends(require_user)])


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
    uso_cfdi: Optional[str] = None,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> list[FacturaListResponse]:
    repo = SqlFacturaRepository(db)
    use_case = ListFacturasUseCase(repo)
    data = ListFacturasInput(
        year=year,
        month=month,
        tipo=tipo,
        naturaleza=naturaleza,
        uso_cfdi=uso_cfdi,
        rfc=x_rfc,
    )
    items = use_case.execute(data)
    return factura_list_to_dto(items)


@router.get(
    "/export.csv",
    summary="Exporta facturas a CSV",
    description="Devuelve un CSV con las facturas filtradas.",
)
def export_facturas_csv(
    year: Optional[int] = None,
    month: Optional[int] = None,
    tipo: Optional[str] = None,
    naturaleza: Optional[str] = None,
    uso_cfdi: Optional[str] = None,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> Response:
    repo = SqlFacturaRepository(db)
    use_case = ListFacturasUseCase(repo)
    data = ListFacturasInput(
        year=year,
        month=month,
        tipo=tipo,
        naturaleza=naturaleza,
        uso_cfdi=uso_cfdi,
        rfc=x_rfc,
    )
    items = use_case.execute(data)

    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        [
            "fecha_emision",
            "tipo_comprobante",
            "naturaleza",
            "uuid",
            "emisor_rfc",
            "receptor_rfc",
            "uso_cfdi",
            "total",
            "total_sin_iva",
            "total_trasladados",
            "total_retenidos",
            "moneda",
        ]
    )
    for row in items:
        w.writerow(
            [
                row.fecha_emision.isoformat() if row.fecha_emision else "",
                row.tipo_comprobante or "",
                row.naturaleza or "",
                row.uuid or "",
                row.emisor_rfc or "",
                row.receptor_rfc or "",
                row.uso_cfdi or "",
                f"{row.total:.2f}" if row.total is not None else "",
                f"{(row.total - row.total_trasladados):.2f}"
                if row.total is not None and row.total_trasladados is not None
                else "",
                f"{row.total_trasladados:.2f}" if row.total_trasladados is not None else "",
                f"{row.total_retenidos:.2f}" if row.total_retenidos is not None else "",
                row.moneda or "",
            ]
        )

    filename = "facturas.csv"
    if year and month:
        filename = f"facturas_{year}_{month:02d}.csv"
    return csv_response(out.getvalue(), filename=filename)


@router.get(
    "/{factura_id}",
    response_model=FacturaDetailResponse,
    summary="Detalle de factura",
    description="Devuelve factura con sus conceptos y pagos.",
)
def detalle_factura(
    factura_id: int,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> FacturaDetailResponse:
    factura_repo = SqlFacturaRepository(db)
    concepto_repo = SqlConceptoRepository(db)
    pago_repo = SqlPagoRepository(db)
    use_case = GetFacturaDetailUseCase(factura_repo, concepto_repo, pago_repo)
    result = use_case.execute(GetFacturaDetailInput(factura_id=factura_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if result.factura.emisor_rfc != x_rfc and result.factura.receptor_rfc != x_rfc:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    return factura_detail_to_dto(result)


@router.get(
    "/{factura_id}/xml",
    summary="XML de CFDI",
    description="Devuelve el XML crudo de la factura.",
)
def factura_xml(
    factura_id: int,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> Response:
    repo = SqlFacturaRepository(db)
    use_case = GetFacturaXmlUseCase(repo)
    result = use_case.execute(GetFacturaXmlInput(factura_id=factura_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if result.emisor_rfc != x_rfc and result.receptor_rfc != x_rfc:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return xml_response(result.xml_text)


@router.delete(
    "/{factura_id}",
    summary="Eliminar factura",
    description="Elimina una factura por ID.",
)
def eliminar_factura(
    factura_id: int,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> dict:
    repo = SqlFacturaRepository(db)
    use_case = DeleteFacturaUseCase(repo)
    result = use_case.execute(DeleteFacturaInput(factura_id=factura_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if result.emisor_rfc != x_rfc and result.receptor_rfc != x_rfc:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    if not result.deleted:
        raise HTTPException(status_code=409, detail="No se pudo eliminar la factura")
    return {"ok": True}
