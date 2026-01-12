from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import ConceptoModel
from app.application.facturas.dto import ConceptoItem
from app.ports.conceptos_repo import ConceptoRepository


class SqlConceptoRepository(ConceptoRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_factura(self, factura_id: int) -> list[ConceptoItem]:
        rows = (
            self._db.execute(
                select(ConceptoModel).where(ConceptoModel.factura_id == factura_id)
            )
            .scalars()
            .all()
        )
        return [
            ConceptoItem(
                id=r.id,
                factura_id=r.factura_id,
                clave_prod_serv=r.clave_prod_serv,
                cantidad=float(r.cantidad) if r.cantidad is not None else None,
                clave_unidad=r.clave_unidad,
                descripcion=r.descripcion,
                valor_unitario=float(r.valor_unitario) if r.valor_unitario is not None else None,
                importe=float(r.importe) if r.importe is not None else None,
                objeto_imp=r.objeto_imp,
            )
            for r in rows
        ]
