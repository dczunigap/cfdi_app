from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.mappers import declaracion_to_list_item
from app.adapters.outbound.db.models import DeclaracionModel
from app.ports.declaraciones_repo import DeclaracionRepository
from app.application.declaraciones.dto import DeclaracionListItem
from app.domain.declaraciones.entities import DeclaracionPDF


class SqlDeclaracionRepository(DeclaracionRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_declaraciones(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[DeclaracionListItem]:
        q = select(DeclaracionModel)
        if year is not None:
            q = q.where(DeclaracionModel.year == year)
        if month is not None:
            q = q.where(DeclaracionModel.month == month)
        rows = self._db.execute(q).scalars().all()
        return [declaracion_to_list_item(r) for r in rows]

    def exists_sha256(self, sha256: str) -> bool:
        if not sha256:
            return False
        return (
            self._db.execute(
                select(DeclaracionModel.id).where(DeclaracionModel.sha256 == sha256)
            )
            .first()
            is not None
        )

    def add_declaracion(self, declaracion: DeclaracionPDF) -> None:
        model = DeclaracionModel(
            year=declaracion.year,
            month=declaracion.month,
            rfc=declaracion.rfc,
            folio=declaracion.folio,
            fecha_presentacion=declaracion.fecha_presentacion,
            sha256=declaracion.sha256,
            filename=declaracion.filename,
            original_name=declaracion.original_name,
            num_pages=declaracion.num_pages,
            text_excerpt=declaracion.text_excerpt,
        )
        self._db.add(model)
        self._db.commit()

    def get_by_id(self, declaracion_id: int) -> DeclaracionModel | None:
        return self._db.get(DeclaracionModel, declaracion_id)
