from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class SatDescargaCreateRequest(BaseModel):
    kind: str = "cfdi"
    tipo_solicitud: str = "emitidos"
    fecha_inicial: datetime
    fecha_final: datetime
    rfc_emisor: str | None = None
    rfc_receptor: str | None = None
    rfc_a_cuenta_terceros: str | None = None
    tipo_comprobante: str | None = None
    complemento: str | None = None
    estado_comprobante: str | None = None
    folio: str | None = None
    uuid: str | None = None
    rfc_receptores: list[str] = Field(default_factory=list)


class SatDescargaResponse(BaseModel):
    id: int
    rfc: str
    kind: str
    tipo_solicitud: str
    anio_filtro: int | None = None
    mes_filtro: int | None = None
    id_solicitud: str | None = None
    estado: str
    paquetes: list[str] = Field(default_factory=list)
    link_descarga: str | None = None
    zip_path: str | None = None
    attempts: int
    next_check_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
