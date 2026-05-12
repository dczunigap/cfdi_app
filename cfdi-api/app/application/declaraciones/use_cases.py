from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.declaraciones.dto import DeclaracionDetail, DeclaracionListItem
from app.ports.declaraciones_repo import DeclaracionRepository


@dataclass
class ListDeclaracionesInput:
    year: Optional[int] = None
    month: Optional[int] = None
    rfc: Optional[str] = None


class ListDeclaracionesUseCase:
    def __init__(self, repo: DeclaracionRepository) -> None:
        self._repo = repo

    def execute(self, data: ListDeclaracionesInput) -> list[DeclaracionListItem]:
        return self._repo.list_declaraciones(year=data.year, month=data.month, rfc=data.rfc)


@dataclass
class GetDeclaracionDetailInput:
    declaracion_id: int


class GetDeclaracionDetailUseCase:
    def __init__(self, repo: DeclaracionRepository) -> None:
        self._repo = repo

    def execute(self, data: GetDeclaracionDetailInput) -> DeclaracionDetail | None:
        dec = self._repo.get_by_id(data.declaracion_id)
        if dec is None:
            return None

        return DeclaracionDetail(
            id=dec.id,
            year=dec.year,
            month=dec.month,
            rfc=dec.rfc,
            folio=dec.folio,
            fecha_presentacion=dec.fecha_presentacion,
            cantidad_a_cargo=float(dec.cantidad_a_cargo) if dec.cantidad_a_cargo is not None else 0.0,
            saldo_a_favor=float(dec.saldo_a_favor) if dec.saldo_a_favor is not None else 0.0,
            saldo_a_pagar=float(dec.saldo_a_pagar) if dec.saldo_a_pagar is not None else 0.0,
            filename=dec.filename,
            original_name=dec.original_name,
            num_pages=dec.num_pages,
            sha256=dec.sha256,
            text_excerpt=dec.text_excerpt,
        )
