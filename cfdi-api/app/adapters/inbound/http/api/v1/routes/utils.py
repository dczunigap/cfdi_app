from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.domain.declaraciones.entities import DeclaracionPDF


def get_or_404(db: Session, model, obj_id: int, label: str):
    obj = db.get(model, obj_id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{label} no encontrada")
    return obj


def declaracion_model_to_entity(model) -> DeclaracionPDF:
    return DeclaracionPDF(
        year=model.year,
        month=model.month,
        rfc=model.rfc,
        folio=model.folio,
        fecha_presentacion=model.fecha_presentacion,
        sha256=model.sha256,
        filename=model.filename,
        original_name=model.original_name,
        num_pages=model.num_pages,
        text_excerpt=model.text_excerpt,
        created_at=model.created_at,
    )


def xml_response(content: str) -> Response:
    return Response(
        content=content,
        media_type="application/xml; charset=utf-8",
    )


def pdf_inline_response(content: bytes, filename: str) -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


def json_response(content: str) -> Response:
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
    )


def text_response(content: str, filename: str | None = None) -> Response:
    headers = {"Content-Disposition": f"attachment; filename={filename}"} if filename else None
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers=headers,
    )


def csv_response(content: str, filename: str | None = None) -> Response:
    headers = {"Content-Disposition": f"attachment; filename={filename}"} if filename else None
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )
