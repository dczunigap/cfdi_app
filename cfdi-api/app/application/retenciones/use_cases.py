from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.retenciones.dto import RetencionDetail, RetencionListItem
from app.ports.retenciones_repo import RetencionRepository


@dataclass
class ListRetencionesInput:
    year: Optional[int] = None
    month: Optional[int] = None


class ListRetencionesUseCase:
    def __init__(self, repo: RetencionRepository) -> None:
        self._repo = repo

    def execute(self, data: ListRetencionesInput) -> list[RetencionListItem]:
        return self._repo.list_retenciones(year=data.year, month=data.month)


@dataclass
class GetRetencionDetailInput:
    retencion_id: int


class GetRetencionDetailUseCase:
    def __init__(self, repo: RetencionRepository) -> None:
        self._repo = repo

    def execute(self, data: GetRetencionDetailInput) -> RetencionDetail | None:
        retencion = self._repo.get_by_id(data.retencion_id)
        if retencion is None:
            return None

        return RetencionDetail(
            id=retencion.id,
            uuid=retencion.uuid,
            fecha_exp=retencion.fecha_exp,
            ejercicio=retencion.ejercicio,
            mes_ini=retencion.mes_ini,
            mes_fin=retencion.mes_fin,
            emisor_rfc=retencion.emisor_rfc,
            emisor_nombre=retencion.emisor_nombre,
            receptor_rfc=retencion.receptor_rfc,
            receptor_nombre=retencion.receptor_nombre,
            mon_tot_serv_siva=float(retencion.mon_tot_serv_siva)
            if retencion.mon_tot_serv_siva is not None
            else None,
            total_iva_trasladado=float(retencion.total_iva_trasladado)
            if retencion.total_iva_trasladado is not None
            else None,
            total_iva_retenido=float(retencion.total_iva_retenido)
            if retencion.total_iva_retenido is not None
            else None,
            total_isr_retenido=float(retencion.total_isr_retenido)
            if retencion.total_isr_retenido is not None
            else None,
            mon_total_por_uso_plataforma=float(retencion.mon_total_por_uso_plataforma)
            if retencion.mon_total_por_uso_plataforma is not None
            else None,
            xml_text=retencion.xml_text,
        )
