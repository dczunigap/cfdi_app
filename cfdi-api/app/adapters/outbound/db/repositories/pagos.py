from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import PagoModel
from app.application.facturas.dto import PagoItem
from app.ports.pagos_repo import PagoRepository


class SqlPagoRepository(PagoRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_factura(self, factura_id: int) -> list[PagoItem]:
        rows = (
            self._db.execute(select(PagoModel).where(PagoModel.factura_id == factura_id))
            .scalars()
            .all()
        )
        return [
            PagoItem(
                id=r.id,
                factura_id=r.factura_id,
                fecha_pago=r.fecha_pago,
                year_pago=r.year_pago,
                month_pago=r.month_pago,
                monto=float(r.monto) if r.monto is not None else None,
                moneda_p=r.moneda_p,
                forma_pago_p=r.forma_pago_p,
            )
            for r in rows
        ]
