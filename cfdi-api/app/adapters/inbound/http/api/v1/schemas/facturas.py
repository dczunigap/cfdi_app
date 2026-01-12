from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FacturaListResponse(BaseModel):
    id: Optional[int]
    uuid: Optional[str]
    fecha_emision: Optional[datetime]
    tipo_comprobante: Optional[str]
    year_emision: Optional[int]
    month_emision: Optional[int]
    emisor_rfc: Optional[str]
    emisor_nombre: Optional[str]
    receptor_rfc: Optional[str]
    receptor_nombre: Optional[str]
    uso_cfdi: Optional[str]
    moneda: Optional[str]
    subtotal: Optional[float]
    descuento: Optional[float]
    total: Optional[float]
    total_trasladados: Optional[float]
    total_retenidos: Optional[float]
    naturaleza: Optional[str]


class ConceptoResponse(BaseModel):
    id: Optional[int]
    factura_id: int
    clave_prod_serv: Optional[str]
    cantidad: Optional[float]
    clave_unidad: Optional[str]
    descripcion: Optional[str]
    valor_unitario: Optional[float]
    importe: Optional[float]
    objeto_imp: Optional[str]


class PagoResponse(BaseModel):
    id: Optional[int]
    factura_id: int
    fecha_pago: Optional[datetime]
    year_pago: Optional[int]
    month_pago: Optional[int]
    monto: Optional[float]
    moneda_p: Optional[str]
    forma_pago_p: Optional[str]


class FacturaDetailResponse(BaseModel):
    factura: FacturaListResponse
    conceptos: list[ConceptoResponse]
    pagos: list[PagoResponse]
