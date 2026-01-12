from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RetencionPlataforma:
    uuid: Optional[str] = None
    version: Optional[str] = None
    fecha_exp: Optional[datetime] = None
    ejercicio: Optional[int] = None
    mes_ini: Optional[int] = None
    mes_fin: Optional[int] = None
    emisor_rfc: Optional[str] = None
    emisor_nombre: Optional[str] = None
    receptor_rfc: Optional[str] = None
    receptor_nombre: Optional[str] = None
    monto_tot_operacion: Optional[float] = None
    monto_tot_grav: Optional[float] = None
    monto_tot_exent: Optional[float] = None
    monto_tot_ret: Optional[float] = None
    periodicidad: Optional[str] = None
    num_serv: Optional[int] = None
    mon_tot_serv_siva: Optional[float] = None
    total_iva_trasladado: Optional[float] = None
    total_iva_retenido: Optional[float] = None
    total_isr_retenido: Optional[float] = None
    dif_iva_entregado_prest_serv: Optional[float] = None
    mon_total_por_uso_plataforma: Optional[float] = None
    xml_text: Optional[str] = None
