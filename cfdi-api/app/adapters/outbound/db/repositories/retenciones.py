from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.mappers import retencion_to_list_item
from app.adapters.outbound.db.models import RetencionModel
from app.ports.retenciones_repo import RetencionRepository
from app.application.retenciones.dto import RetencionListItem
from app.domain.retenciones.entities import RetencionPlataforma


class SqlRetencionRepository(RetencionRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_retenciones(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[RetencionListItem]:
        q = select(RetencionModel)
        if year is not None:
            q = q.where(RetencionModel.ejercicio == year)
        if month is not None:
            q = q.where(RetencionModel.mes_fin == month)
        rows = self._db.execute(q).scalars().all()
        return [retencion_to_list_item(r) for r in rows]

    def exists_uuid(self, uuid: str) -> bool:
        if not uuid:
            return False
        return (
            self._db.execute(select(RetencionModel.id).where(RetencionModel.uuid == uuid))
            .first()
            is not None
        )

    def add_retencion(self, retencion: RetencionPlataforma) -> None:
        model = RetencionModel(
            uuid=retencion.uuid,
            version=retencion.version,
            fecha_exp=retencion.fecha_exp,
            ejercicio=retencion.ejercicio,
            mes_ini=retencion.mes_ini,
            mes_fin=retencion.mes_fin,
            emisor_rfc=retencion.emisor_rfc,
            emisor_nombre=retencion.emisor_nombre,
            receptor_rfc=retencion.receptor_rfc,
            receptor_nombre=retencion.receptor_nombre,
            monto_tot_operacion=retencion.monto_tot_operacion,
            monto_tot_grav=retencion.monto_tot_grav,
            monto_tot_exent=retencion.monto_tot_exent,
            monto_tot_ret=retencion.monto_tot_ret,
            periodicidad=retencion.periodicidad,
            num_serv=retencion.num_serv,
            mon_tot_serv_siva=retencion.mon_tot_serv_siva,
            total_iva_trasladado=retencion.total_iva_trasladado,
            total_iva_retenido=retencion.total_iva_retenido,
            total_isr_retenido=retencion.total_isr_retenido,
            dif_iva_entregado_prest_serv=retencion.dif_iva_entregado_prest_serv,
            mon_total_por_uso_plataforma=retencion.mon_total_por_uso_plataforma,
            xml_text=retencion.xml_text or "",
        )
        self._db.add(model)
        self._db.commit()

    def get_by_id(self, retencion_id: int) -> RetencionModel | None:
        return self._db.get(RetencionModel, retencion_id)
