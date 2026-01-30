from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SatCredential:
    rfc: str
    pfx_encrypted: bytes
    pfx_password_encrypted: str | None
    created_at: datetime
    updated_at: datetime | None


@dataclass
class SatDescarga:
    id: int
    rfc: str
    kind: str
    tipo_solicitud: str
    anio_filtro: int | None
    mes_filtro: int | None
    id_solicitud: str | None
    estado: str
    paquetes: list[str]
    link_descarga: str | None
    zip_path: str | None
    attempts: int
    next_check_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime | None
