from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.adapters.inbound.http.api.v1.schemas.declaraciones import (
    DeclaracionDetailResponse,
    DeclaracionListResponse,
)
from app.adapters.outbound.db.models import DeclaracionModel
from app.adapters.outbound.db.repositories.declaraciones import SqlDeclaracionRepository
from app.adapters.inbound.http.deps import get_db
from app.adapters.outbound.files.pdf_storage import LocalPdfStorage
from app.adapters.services.parsers.pdf_parser import LocalPdfParser
from app.application.declaraciones.use_cases import (
    GetDeclaracionDetailInput,
    GetDeclaracionDetailUseCase,
    ListDeclaracionesInput,
    ListDeclaracionesUseCase,
)
from app.application.declaraciones.payload import build_declaracion_payload
from app.domain.declaraciones.entities import DeclaracionPDF
from app.utils.json import serialize_to_json

router = APIRouter(prefix="/declaraciones", tags=["declaraciones"])


@router.get(
    "/",
    response_model=list[DeclaracionListResponse],
    summary="Lista declaraciones",
    description="Devuelve declaraciones filtradas por year y month.",
)
def listar_declaraciones(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
) -> list[DeclaracionListResponse]:
    repo = SqlDeclaracionRepository(db)
    use_case = ListDeclaracionesUseCase(repo)
    data = ListDeclaracionesInput(year=year, month=month)
    items = use_case.execute(data)
    return [DeclaracionListResponse(**item.__dict__) for item in items]


@router.get(
    "/{dec_id}",
    response_model=DeclaracionDetailResponse,
    summary="Detalle de declaracion",
    description="Devuelve el detalle de la declaracion PDF.",
)
def detalle_declaracion(dec_id: int, db: Session = Depends(get_db)) -> DeclaracionDetailResponse:
    repo = SqlDeclaracionRepository(db)
    use_case = GetDeclaracionDetailUseCase(repo)
    result = use_case.execute(GetDeclaracionDetailInput(declaracion_id=dec_id))
    if result is None:
        raise HTTPException(status_code=404, detail="No encontrada")
    return DeclaracionDetailResponse(**result.__dict__)


@router.get(
    "/{dec_id}/archivo/{filename}",
    summary="Descarga PDF de declaracion",
    description="Devuelve el PDF almacenado para la declaracion indicada.",
)
def descargar_declaracion_pdf(
    dec_id: int,
    filename: str,
    db: Session = Depends(get_db),
) -> Response:
    dec = db.get(DeclaracionModel, dec_id)
    if not dec:
        raise HTTPException(status_code=404, detail="No encontrada")

    base_dir = Path(__file__).resolve().parents[7]
    storage = LocalPdfStorage(base_dir / "database" / "pdfs")
    if not dec.filename:
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")
    if filename != dec.filename:
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")
    try:
        content = storage.read(filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get(
    "/{dec_id}/resumen.json",
    summary="Resumen de declaracion",
    description="Devuelve el payload JSON extraido del PDF de declaracion.",
)
def declaracion_pdf_resumen_json(dec_id: int, db: Session = Depends(get_db)) -> Response:
    dec = db.get(DeclaracionModel, dec_id)
    if not dec:
        raise HTTPException(status_code=404, detail="No encontrada")

    dec_entity = DeclaracionPDF(
        year=dec.year,
        month=dec.month,
        rfc=dec.rfc,
        folio=dec.folio,
        fecha_presentacion=dec.fecha_presentacion,
        sha256=dec.sha256,
        filename=dec.filename,
        original_name=dec.original_name,
        num_pages=dec.num_pages,
        text_excerpt=dec.text_excerpt,
        created_at=dec.created_at,
    )

    parser = LocalPdfParser()
    payload = build_declaracion_payload(dec_entity, parser.parse_sat_summary)
    return Response(
        content=serialize_to_json(payload),
        media_type="application/json; charset=utf-8",
    )
