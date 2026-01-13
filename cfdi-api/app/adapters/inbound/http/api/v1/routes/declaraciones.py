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
from app.adapters.inbound.http.api.v1.mappers import (
    declaracion_detail_to_dto,
    declaracion_list_to_dto,
)
from app.adapters.outbound.db.models import DeclaracionModel
from app.adapters.inbound.http.api.v1.routes.utils import (
    declaracion_model_to_entity,
    get_or_404,
    json_response,
    pdf_inline_response,
)
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
    return declaracion_list_to_dto(items)


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
    return declaracion_detail_to_dto(result)


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
    dec = get_or_404(db, DeclaracionModel, dec_id, "Declaracion")

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

    return pdf_inline_response(content, filename)


@router.get(
    "/{dec_id}/resumen.json",
    summary="Resumen de declaracion",
    description="Devuelve el payload JSON extraido del PDF de declaracion.",
)
def declaracion_pdf_resumen_json(dec_id: int, db: Session = Depends(get_db)) -> Response:
    dec = get_or_404(db, DeclaracionModel, dec_id, "Declaracion")

    dec_entity = declaracion_model_to_entity(dec)

    parser = LocalPdfParser()
    payload = build_declaracion_payload(dec_entity, parser.parse_sat_summary)
    return json_response(serialize_to_json(payload))
