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
    receptor_rfc: Optional[str]
    monto_tot_ret: Optional[float]
    total_iva_trasladado: Optional[float]
    total_iva_retenido: Optional[float]
    total_isr_retenido: Optional[float]
