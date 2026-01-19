from __future__ import annotations

import base64
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from sat_actions import SOAP_CFDI_ACTION_AUTENTICA, SOAP_ACTION_DESCARGA, SOAP_CFDI_ACTION_VERIFICA
from sat_descarga_requests import (
    SolicitudDescargaParams,
    build_descarga_paquete_envelope,
    build_solicitud_descarga_envelope,
    build_verificacion_envelope,
)
from sat_descarga_service import SatDescargaSoapService
from sat_ws_security import SatKeyMaterial, build_auth_envelope, load_sat_key_material


@dataclass(frozen=True)
class VerificacionResult:
    estado_solicitud: str | None
    codigo_estado: str | None
    numero_cfdis: str | None
    mensaje: str | None
    paquetes: list[str]


class SatDescargaWorkflow:
    def __init__(self, service: SatDescargaSoapService, key_material: SatKeyMaterial) -> None:
        self._service = service
        self._key_material = key_material

    @staticmethod
    def from_paths(
        service: SatDescargaSoapService,
        cert_path: str,
        key_path: str,
        key_password: str | None,
    ) -> "SatDescargaWorkflow":
        key_material = load_sat_key_material(cert_path, key_path, key_password)
        return SatDescargaWorkflow(service=service, key_material=key_material)

    def autenticar(
        self,
        soap_action: str | None = None,
        to_url: str | None = None,
        action: str | None = None,
    ) -> str:
        envelope = build_auth_envelope(self._key_material, to_url=to_url, action=action)
        response = self._service.autenticar(envelope, soap_action=soap_action or SOAP_CFDI_ACTION_AUTENTICA)
        return extract_auth_token(response)

    def solicitar_descarga(
        self,
        params: SolicitudDescargaParams,
        access_token: str,
        soap_action: str | None = None,
        tag_name: str = "SolicitaDescargaEmitidos",
    ) -> str:
        envelope = build_solicitud_descarga_envelope(params, self._key_material, tag_name=tag_name)
        response = self._service.solicitar_descarga(
            envelope, soap_action=soap_action, access_token=access_token
        )
        result_tag = _result_tag_for_solicita(tag_name)
        return extract_id_solicitud(response, result_tag=result_tag)

    def verificar_descarga(
        self,
        rfc_solicitante: str,
        id_solicitud: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> VerificacionResult:
        envelope = build_verificacion_envelope(rfc_solicitante, id_solicitud, self._key_material)
        response = self._service.verificar_descarga(
            envelope, soap_action=soap_action or SOAP_CFDI_ACTION_VERIFICA, access_token=access_token
        )
        return extract_verificacion_result(response)

    def descargar_paquete(
        self,
        rfc_solicitante: str,
        id_paquete: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> bytes:
        envelope = build_descarga_paquete_envelope(rfc_solicitante, id_paquete)
        response = self._service.descargar_paquete(
            envelope, soap_action=soap_action or SOAP_ACTION_DESCARGA, access_token=access_token
        )
        return extract_descarga_zip(response)


def extract_auth_token(xml_text: str) -> str:
    root = ET.fromstring(xml_text)
    result = _find_text(root, "AutenticaResult")
    if not result:
        raise ValueError("No se encontro AutenticaResult en la respuesta.")
    return result


def extract_id_solicitud(
    xml_text: str,
    result_tag: str = "SolicitaDescargaResult",
) -> str:
    root = ET.fromstring(xml_text)
    result_node = _find_node(root, result_tag)
    if result_node is None:
        raise ValueError(f"No se encontro {result_tag} en la respuesta.")
    id_solicitud = result_node.attrib.get("IdSolicitud")
    if not id_solicitud:
        raise ValueError("Respuesta sin IdSolicitud.")
    return id_solicitud


def _result_tag_for_solicita(tag_name: str) -> str:
    if tag_name == "SolicitaDescargaRecibidos":
        return "SolicitaDescargaRecibidosResult"
    return "SolicitaDescargaEmitidosResult"


def extract_verificacion_result(xml_text: str) -> VerificacionResult:
    root = ET.fromstring(xml_text)
    node = _find_node(root, "VerificaSolicitudDescargaResult")
    if node is None:
        raise ValueError("No se encontro VerificaSolicitudDescargaResult en la respuesta.")
    paquetes = [child.text for child in node.findall(".//{*}IdsPaquetes") if child.text]
    return VerificacionResult(
        estado_solicitud=node.attrib.get("EstadoSolicitud"),
        codigo_estado=node.attrib.get("CodigoEstadoSolicitud") or node.attrib.get("CodEstatus"),
        numero_cfdis=node.attrib.get("NumeroCFDIs"),
        mensaje=node.attrib.get("Mensaje"),
        paquetes=paquetes,
    )


def extract_descarga_zip(xml_bytes: bytes) -> bytes:
    root = ET.fromstring(xml_bytes)
    result = _find_text(root, "DescargaMasivaResult")
    if not result:
        raise ValueError("No se encontro DescargaMasivaResult en la respuesta.")
    return base64.b64decode(result)


def _find_text(root: ET.Element, tag_name: str) -> str | None:
    node = _find_node(root, tag_name)
    if node is None or not node.text:
        return None
    return node.text.strip()


def _find_node(root: ET.Element, tag_name: str) -> ET.Element | None:
    for node in root.iter():
        if node.tag.endswith(tag_name):
            return node
    return None
