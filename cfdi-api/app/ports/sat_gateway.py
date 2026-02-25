from __future__ import annotations

from typing import Protocol

from typing import Any

from app.application.sat.dto import (
    DescargaPaqueteResult,
    SolicitudDescargaParams,
    SolicitudDescargaResult,
    VerificacionResult,
)


class SatGateway(Protocol):
    def load_key_material(self, pfx_bytes: bytes, password: str | None) -> Any:
        ...

    def autenticar(
        self,
        kind: str,
        key_material: Any,
        soap_action: str | None = None,
        to_url: str | None = None,
        action: str | None = None,
    ) -> str:
        ...

    def solicitar_descarga(
        self,
        kind: str,
        key_material: Any,
        params: SolicitudDescargaParams,
        access_token: str,
        soap_action: str | None = None,
        tag_name: str = "SolicitaDescargaEmitidos",
    ) -> SolicitudDescargaResult:
        ...

    def verificar_descarga(
        self,
        kind: str,
        key_material: Any,
        rfc_solicitante: str,
        id_solicitud: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> VerificacionResult:
        ...

    def descargar_paquete(
        self,
        kind: str,
        key_material: Any,
        rfc_solicitante: str,
        id_paquete: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> DescargaPaqueteResult:
        ...
