from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.retenciones.dto import RetencionListItem
from app.ports.retenciones_repo import RetencionRepository


@dataclass
class ListRetencionesInput:
    year: Optional[int] = None
    month: Optional[int] = None


class ListRetencionesUseCase:
    def __init__(self, repo: RetencionRepository) -> None:
        self._repo = repo

    def execute(self, data: ListRetencionesInput) -> list[RetencionListItem]:
        return self._repo.list_retenciones(year=data.year, month=data.month)
