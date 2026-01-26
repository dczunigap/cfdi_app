from __future__ import annotations

from app.adapters.services.sat.pkcs12.pfx import load_key_material_from_pfx_bytes
from app.application.sat.dto import SolicitudDescargaParams, VerificacionResult
from app.adapters.services.sat.soap.descarga_service import SatDescargaSoapService
from app.adapters.services.sat.soap.descarga_workflow import SatDescargaWorkflow
from app.adapters.services.sat.soap.endpoints import SatEndpoints
from app.adapters.services.sat.wsse.ws_security import SatKeyMaterial
from app.ports.sat_gateway import SatGateway


class SoapSatGateway(SatGateway):
    def load_key_material(self, pfx_bytes: bytes, password: str | None) -> SatKeyMaterial:
        return load_key_material_from_pfx_bytes(pfx_bytes, password)

    def autenticar(
        self,
        kind: str,
        key_material: SatKeyMaterial,
        soap_action: str | None = None,
        to_url: str | None = None,
        action: str | None = None,
    ) -> str:
        workflow = self._workflow(kind, key_material)
        return workflow.autenticar(
            soap_action=soap_action,
            to_url=to_url,
            action=action,
        )

    def solicitar_descarga(
        self,
        kind: str,
        key_material: SatKeyMaterial,
        params: SolicitudDescargaParams,
        access_token: str,
        soap_action: str | None = None,
        tag_name: str = "SolicitaDescargaEmitidos",
    ) -> str:
        workflow = self._workflow(kind, key_material)
        return workflow.solicitar_descarga(
            params=params,
            access_token=access_token,
            soap_action=soap_action,
            tag_name=tag_name,
        )

    def verificar_descarga(
        self,
        kind: str,
        key_material: SatKeyMaterial,
        rfc_solicitante: str,
        id_solicitud: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> VerificacionResult:
        workflow = self._workflow(kind, key_material)
        return workflow.verificar_descarga(
            rfc_solicitante=rfc_solicitante,
            id_solicitud=id_solicitud,
            access_token=access_token,
            soap_action=soap_action,
        )

    def descargar_paquete(
        self,
        kind: str,
        key_material: SatKeyMaterial,
        rfc_solicitante: str,
        id_paquete: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> bytes:
        workflow = self._workflow(kind, key_material)
        return workflow.descargar_paquete(
            rfc_solicitante=rfc_solicitante,
            id_paquete=id_paquete,
            access_token=access_token,
            soap_action=soap_action,
        )

    @staticmethod
    def _workflow(kind: str, key_material: SatKeyMaterial) -> SatDescargaWorkflow:
        endpoints = SatEndpoints.for_kind(kind)
        service = SatDescargaSoapService(endpoints)
        return SatDescargaWorkflow(service=service, key_material=key_material)
