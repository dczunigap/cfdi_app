from __future__ import annotations

from typing import Protocol

from app.application.facturas.dto import ConceptoItem


class ConceptoRepository(Protocol):
    def list_by_factura(self, factura_id: int) -> list[ConceptoItem]:
        ...
