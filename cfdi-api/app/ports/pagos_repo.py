from __future__ import annotations

from typing import Protocol

from app.application.facturas.dto import PagoItem


class PagoRepository(Protocol):
    def list_by_factura(self, factura_id: int) -> list[PagoItem]:
        ...
