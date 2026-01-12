from __future__ import annotations

from typing import Optional, Protocol

from app.application.retenciones.dto import RetencionListItem


class RetencionRepository(Protocol):
    def list_retenciones(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[RetencionListItem]:
        ...

    def exists_uuid(self, uuid: str) -> bool:
        ...

    def add_retencion(self, retencion) -> None:
        ...
