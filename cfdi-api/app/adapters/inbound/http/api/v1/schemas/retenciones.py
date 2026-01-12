from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RetencionListResponse(BaseModel):
    id: Optional[int]
    uuid: Optional[str]
    fecha_exp: Optional[datetime]
    ejercicio: Optional[int]
    mes_ini: Optional[int]
    mes_fin: Optional[int]
    emisor_rfc: Optional[str]
    emisor_nombre: Optional[str]
    receptor_rfc: Optional[str]
    mon_tot_serv_siva: Optional[float]
    total_iva_trasladado: Optional[float]
    total_iva_retenido: Optional[float]
    total_isr_retenido: Optional[float]


class RetencionDetailResponse(BaseModel):
    id: Optional[int]
    uuid: Optional[str]
    fecha_exp: Optional[datetime]
    ejercicio: Optional[int]
    mes_ini: Optional[int]
    mes_fin: Optional[int]
    emisor_rfc: Optional[str]
    emisor_nombre: Optional[str]
    receptor_rfc: Optional[str]
    receptor_nombre: Optional[str]
    mon_tot_serv_siva: Optional[float]
    total_iva_trasladado: Optional[float]
    total_iva_retenido: Optional[float]
    total_isr_retenido: Optional[float]
    mon_total_por_uso_plataforma: Optional[float]
    xml_text: Optional[str]
