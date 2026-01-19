from __future__ import annotations

from dataclasses import dataclass

from config import (
    SAT_CFDI_AUTH_URL,
    SAT_CFDI_SOLICITUD_URL,
    SAT_CFDI_VERIFICACION_URL,
    SAT_CFDI_DESCARGA_URL,
    SAT_RET_AUTH_URL,
    SAT_RET_SOLICITUD_URL,
    SAT_RET_VERIFICACION_URL,
    SAT_RET_DESCARGA_URL,
)


@dataclass(frozen=True)
class SatEndpoints:
    auth_url: str
    solicitud_url: str
    verificacion_url: str
    descarga_url: str

    @staticmethod
    def for_kind(kind: str) -> "SatEndpoints":
        normalized = kind.strip().lower()
        if normalized == "cfdi":
            return SatEndpoints(
                auth_url=SAT_CFDI_AUTH_URL,
                solicitud_url=SAT_CFDI_SOLICITUD_URL,
                verificacion_url=SAT_CFDI_VERIFICACION_URL,
                descarga_url=SAT_CFDI_DESCARGA_URL,
            )
        if normalized in {"retenciones", "retencion", "ret"}:
            return SatEndpoints(
                auth_url=SAT_RET_AUTH_URL,
                solicitud_url=SAT_RET_SOLICITUD_URL,
                verificacion_url=SAT_RET_VERIFICACION_URL,
                descarga_url=SAT_RET_DESCARGA_URL,
            )
        raise ValueError(f"Tipo SAT no soportado: {kind}")
