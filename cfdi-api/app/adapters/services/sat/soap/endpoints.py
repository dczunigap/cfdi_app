from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


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
                auth_url=settings.sat_cfdi_auth_url,
                solicitud_url=settings.sat_cfdi_solicitud_url,
                verificacion_url=settings.sat_cfdi_verificacion_url,
                descarga_url=settings.sat_cfdi_descarga_url,
            )
        if normalized in {"retenciones", "retencion", "ret"}:
            return SatEndpoints(
                auth_url=settings.sat_ret_auth_url,
                solicitud_url=settings.sat_ret_solicitud_url,
                verificacion_url=settings.sat_ret_verificacion_url,
                descarga_url=settings.sat_ret_descarga_url,
            )
        raise ValueError(f"Tipo SAT no soportado: {kind}")
