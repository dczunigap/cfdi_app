from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.mappers import factura_to_list_item
from app.adapters.outbound.db.models import ConceptoModel, FacturaModel, PagoModel
from app.ports.facturas_repo import FacturaRepository
from app.application.facturas.dto import FacturaListItem
from app.domain.facturas.entities import Factura


class SqlFacturaRepository(FacturaRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_facturas(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        tipo: Optional[str] = None,
        naturaleza: Optional[str] = None,
    ) -> list[FacturaListItem]:
        q = select(FacturaModel)
        if year is not None:
            q = q.where(FacturaModel.year_emision == year)
        if month is not None:
            q = q.where(FacturaModel.month_emision == month)
        if naturaleza:
            q = q.where(FacturaModel.naturaleza == naturaleza)
        if tipo:
            q = q.where(FacturaModel.tipo_comprobante == tipo.upper())
        rows = self._db.execute(q).scalars().all()
        return [factura_to_list_item(r) for r in rows]

    def exists_uuid(self, uuid: str) -> bool:
        if not uuid:
            return False
        return (
            self._db.execute(select(FacturaModel.id).where(FacturaModel.uuid == uuid))
            .first()
            is not None
        )

    def add_factura(self, factura: Factura) -> None:
        model = FacturaModel(
            uuid=factura.uuid,
            version=factura.version,
            tipo_comprobante=factura.tipo_comprobante,
            fecha_emision=factura.fecha_emision,
            year_emision=factura.year_emision,
            month_emision=factura.month_emision,
            naturaleza=factura.naturaleza,
            emisor_rfc=factura.emisor_rfc,
            emisor_nombre=factura.emisor_nombre,
            receptor_rfc=factura.receptor_rfc,
            receptor_nombre=factura.receptor_nombre,
            uso_cfdi=factura.uso_cfdi,
            moneda=factura.moneda,
            metodo_pago=factura.metodo_pago,
            forma_pago=factura.forma_pago,
            subtotal=factura.subtotal,
            descuento=factura.descuento,
            total=factura.total,
            total_trasladados=factura.total_trasladados,
            total_retenidos=factura.total_retenidos,
            xml_text=factura.xml_text or "",
        )

        model.conceptos = [
            ConceptoModel(
                clave_prod_serv=c.clave_prod_serv,
                cantidad=c.cantidad,
                clave_unidad=c.clave_unidad,
                descripcion=c.descripcion,
                valor_unitario=c.valor_unitario,
                importe=c.importe,
                objeto_imp=c.objeto_imp,
            )
            for c in factura.conceptos
        ]

        model.pagos = [
            PagoModel(
                fecha_pago=p.fecha_pago,
                year_pago=p.year_pago,
                month_pago=p.month_pago,
                monto=p.monto,
                moneda_p=p.moneda_p,
                forma_pago_p=p.forma_pago_p,
            )
            for p in factura.pagos
        ]

        self._db.add(model)
        self._db.commit()

    def get_by_id(self, factura_id: int) -> FacturaModel | None:
        return self._db.get(FacturaModel, factura_id)
