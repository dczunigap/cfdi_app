from __future__ import annotations

from typing import Optional, Protocol

from app.application.declaraciones.dto import DeclaracionListItem


class DeclaracionRepository(Protocol):
    def list_declaraciones(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[DeclaracionListItem]:
        ...

    def exists_sha256(self, sha256: str) -> bool:
        ...

    def add_declaracion(self, declaracion) -> None:
        ...
