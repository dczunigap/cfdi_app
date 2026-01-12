from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.facturas.dto import ConceptoItem, FacturaDetail, FacturaListItem, PagoItem
from app.ports.facturas_repo import FacturaRepository
from app.ports.conceptos_repo import ConceptoRepository
from app.ports.pagos_repo import PagoRepository


@dataclass
class ListFacturasInput:
    year: Optional[int] = None
    month: Optional[int] = None
    tipo: Optional[str] = None
    naturaleza: Optional[str] = None


class ListFacturasUseCase:
    def __init__(self, repo: FacturaRepository) -> None:
        self._repo = repo

    def execute(self, data: ListFacturasInput) -> list[FacturaListItem]:
        return self._repo.list_facturas(
            year=data.year,
            month=data.month,
            tipo=data.tipo,
            naturaleza=data.naturaleza,
        )


@dataclass
class GetFacturaDetailInput:
    factura_id: int


class GetFacturaDetailUseCase:
    def __init__(
        self,
        factura_repo: FacturaRepository,
        concepto_repo: ConceptoRepository,
        pago_repo: PagoRepository,
    ) -> None:
        self._factura_repo = factura_repo
        self._concepto_repo = concepto_repo
        self._pago_repo = pago_repo

    def execute(self, data: GetFacturaDetailInput) -> FacturaDetail | None:
        factura = self._factura_repo.get_by_id(data.factura_id)
        if factura is None:
            return None

        factura_item = FacturaListItem(
            id=factura.id,
            uuid=factura.uuid,
            fecha_emision=factura.fecha_emision,
            tipo_comprobante=factura.tipo_comprobante,
            year_emision=factura.year_emision,
            month_emision=factura.month_emision,
            emisor_rfc=factura.emisor_rfc,
            emisor_nombre=factura.emisor_nombre,
            receptor_rfc=factura.receptor_rfc,
            receptor_nombre=factura.receptor_nombre,
            uso_cfdi=factura.uso_cfdi,
            moneda=factura.moneda,
            subtotal=float(factura.subtotal) if factura.subtotal is not None else None,
            descuento=float(factura.descuento) if factura.descuento is not None else None,
            total=float(factura.total) if factura.total is not None else None,
            total_trasladados=float(factura.total_trasladados)
            if factura.total_trasladados is not None
            else None,
            total_retenidos=float(factura.total_retenidos)
            if factura.total_retenidos is not None
            else None,
            naturaleza=factura.naturaleza,
        )

        conceptos: list[ConceptoItem] = self._concepto_repo.list_by_factura(factura.id)
        pagos: list[PagoItem] = self._pago_repo.list_by_factura(factura.id)
        return FacturaDetail(factura=factura_item, conceptos=conceptos, pagos=pagos)
