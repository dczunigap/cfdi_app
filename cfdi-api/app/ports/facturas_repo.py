from __future__ import annotations

from typing import Optional, Protocol

from app.application.facturas.dto import FacturaListItem


class FacturaRepository(Protocol):
    def list_facturas(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        tipo: Optional[str] = None,
        naturaleza: Optional[str] = None,
    ) -> list[FacturaListItem]:
        ...

    def exists_uuid(self, uuid: str) -> bool:
        ...

    def add_factura(self, factura) -> None:
        ...

    def get_by_id(self, factura_id: int):
        ...
