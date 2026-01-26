from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SolicitudDescargaParams:
    rfc_solicitante: str
    fecha_inicial: datetime
    fecha_final: datetime
    tipo_solicitud: str
    rfc_emisor: str | None = None
    rfc_receptor: str | None = None
    rfc_a_cuenta_terceros: str | None = None
    tipo_comprobante: str | None = None
    complemento: str | None = None
    estado_comprobante: str | None = None
    folio: str | None = None
    uuid: str | None = None
    rfc_receptores: list[str] = field(default_factory=list)


@dataclass
class VerificacionResult:
    estado_solicitud: str | None
    codigo_estado: str | None
    numero_cfdis: str | None
    mensaje: str | None
    paquetes: list[str]
