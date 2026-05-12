from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.mappers import declaracion_to_list_item
from app.adapters.outbound.db.models import DeclaracionModel
from app.adapters.outbound.db.repositories.utils import apply_optional_filters, exists_by_field
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
        rfc: Optional[str] = None,
    ) -> list[DeclaracionListItem]:
        q = apply_optional_filters(
            select(DeclaracionModel),
            (DeclaracionModel.year, year),
            (DeclaracionModel.month, month),
        )
        rfc_value = (rfc or "").strip().upper()
        if rfc_value:
            q = q.where(DeclaracionModel.rfc == rfc_value)
        rows = self._db.execute(q).scalars().all()
        return [declaracion_to_list_item(r) for r in rows]

    def exists_sha256(self, sha256: str) -> bool:
        return exists_by_field(self._db, DeclaracionModel, DeclaracionModel.sha256, sha256)

    def add_declaracion(self, declaracion: DeclaracionPDF) -> None:
        model = DeclaracionModel(
            year=declaracion.year,
            month=declaracion.month,
            rfc=declaracion.rfc,
            folio=declaracion.folio,
            fecha_presentacion=declaracion.fecha_presentacion,
            cantidad_a_cargo=declaracion.cantidad_a_cargo if declaracion.cantidad_a_cargo is not None else 0,
            saldo_a_favor=declaracion.saldo_a_favor if declaracion.saldo_a_favor is not None else 0,
            saldo_a_pagar=declaracion.saldo_a_pagar if declaracion.saldo_a_pagar is not None else 0,
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
