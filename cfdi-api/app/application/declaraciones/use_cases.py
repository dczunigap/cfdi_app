from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.declaraciones.dto import DeclaracionListItem
from app.ports.declaraciones_repo import DeclaracionRepository


@dataclass
class ListDeclaracionesInput:
    year: Optional[int] = None
    month: Optional[int] = None


class ListDeclaracionesUseCase:
    def __init__(self, repo: DeclaracionRepository) -> None:
        self._repo = repo

    def execute(self, data: ListDeclaracionesInput) -> list[DeclaracionListItem]:
        return self._repo.list_declaraciones(year=data.year, month=data.month)
