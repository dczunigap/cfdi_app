from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RetencionListItem:
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
