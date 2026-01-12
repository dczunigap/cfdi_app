from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Concepto:
    clave_prod_serv: Optional[str] = None
    cantidad: Optional[float] = None
    clave_unidad: Optional[str] = None
    descripcion: Optional[str] = None
    valor_unitario: Optional[float] = None
    importe: Optional[float] = None
    objeto_imp: Optional[str] = None


@dataclass
class Pago:
    fecha_pago: Optional[datetime] = None
    year_pago: Optional[int] = None
    month_pago: Optional[int] = None
    monto: Optional[float] = None
    moneda_p: Optional[str] = None
    forma_pago_p: Optional[str] = None


@dataclass
class Factura:
    uuid: Optional[str] = None
    version: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    fecha_emision: Optional[datetime] = None
    year_emision: Optional[int] = None
    month_emision: Optional[int] = None
    naturaleza: Optional[str] = None
    emisor_rfc: Optional[str] = None
    emisor_nombre: Optional[str] = None
    receptor_rfc: Optional[str] = None
    receptor_nombre: Optional[str] = None
    uso_cfdi: Optional[str] = None
    moneda: Optional[str] = None
    metodo_pago: Optional[str] = None
    forma_pago: Optional[str] = None
    subtotal: Optional[float] = None
    descuento: Optional[float] = None
    total: Optional[float] = None
    total_trasladados: Optional[float] = None
    total_retenidos: Optional[float] = None
    xml_text: Optional[str] = None
    conceptos: list[Concepto] = field(default_factory=list)
    pagos: list[Pago] = field(default_factory=list)
