from __future__ import annotations

import base64
from xml.etree import ElementTree as ET

from app.application.sat.dto import (
    DescargaPaqueteResult,
    SolicitudDescargaParams,
    SolicitudDescargaResult,
    VerificacionResult,
)
from app.adapters.services.sat.soap.actions import SatSoapActions
from app.adapters.services.sat.soap.descarga_requests import (
    build_descarga_paquete_envelope,
    build_solicitud_descarga_envelope,
    build_verificacion_envelope,
)
from app.adapters.services.sat.soap.descarga_service import SatDescargaSoapService
from app.adapters.services.sat.wsse.ws_security import (
    SatKeyMaterial,
    build_auth_envelope,
    load_sat_key_material,
)


class SatDescargaWorkflow:
    def __init__(
        self,
        service: SatDescargaSoapService,
        key_material: SatKeyMaterial,
        actions: SatSoapActions | None = None,
    ) -> None:
        self._service = service
        self._key_material = key_material
        self._actions = actions or SatSoapActions.for_kind("cfdi")

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
        response = self._service.autenticar(envelope, soap_action=soap_action or self._actions.autentica)
        return extract_auth_token(response)

    def solicitar_descarga(
        self,
        params: SolicitudDescargaParams,
        access_token: str,
        soap_action: str | None = None,
        tag_name: str = "SolicitaDescargaEmitidos",
    ) -> SolicitudDescargaResult:
        envelope = build_solicitud_descarga_envelope(params, self._key_material, tag_name=tag_name)
        if not soap_action:
            soap_action = (
                self._actions.solicita_recibidos
                if tag_name == "SolicitaDescargaRecibidos"
                else self._actions.solicita_emitidos
            )
        response = self._service.solicitar_descarga(
            envelope, soap_action=soap_action, access_token=access_token
        )
        result_tag = _result_tag_for_solicita(tag_name)
        return extract_solicitud_result(response, result_tag=result_tag)

    def verificar_descarga(
        self,
        rfc_solicitante: str,
        id_solicitud: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> VerificacionResult:
        envelope = build_verificacion_envelope(rfc_solicitante, id_solicitud, self._key_material)
        response = self._service.verificar_descarga(
            envelope, soap_action=soap_action or self._actions.verifica, access_token=access_token
        )
        return extract_verificacion_result(response)

    def descargar_paquete(
        self,
        rfc_solicitante: str,
        id_paquete: str,
        access_token: str,
        soap_action: str | None = None,
    ) -> DescargaPaqueteResult:
        envelope = build_descarga_paquete_envelope(rfc_solicitante, id_paquete, self._key_material)
        response = self._service.descargar_paquete(
            envelope, soap_action=soap_action or self._actions.descarga, access_token=access_token
        )
        zip_bytes, codigo_estado, mensaje = _extract_descarga_result(response)
        return DescargaPaqueteResult(
            zip_bytes=zip_bytes,
            codigo_estado=codigo_estado,
            mensaje=mensaje,
        )


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


def extract_solicitud_result(
    xml_text: str,
    result_tag: str = "SolicitaDescargaResult",
) -> SolicitudDescargaResult:
    root = ET.fromstring(xml_text)
    result_node = _find_node(root, result_tag)
    if result_node is None:
        raise ValueError(f"No se encontro {result_tag} en la respuesta.")
    return SolicitudDescargaResult(
        id_solicitud=result_node.attrib.get("IdSolicitud"),
        codigo_estado=result_node.attrib.get("CodEstatus"),
        mensaje=result_node.attrib.get("Mensaje"),
    )


def _result_tag_for_solicita(tag_name: str) -> str:
    if tag_name == "SolicitaDescargaRecibidos":
        return "SolicitaDescargaRecibidosResult"
    return "SolicitaDescargaEmitidosResult"


def _should_log_xml_error(
    xml_text: str | bytes,
    *,
    result_tag: str | None = None,
    text_tag: str | None = None,
    code_attr: str | None = None,
    require_id_attr: str | None = None,
) -> bool:
    root = ET.fromstring(xml_text)
    if _find_node(root, "Fault") is not None:
        return True
    if result_tag:
        result_node = _find_node(root, result_tag)
        if result_node is None:
            return True
        if code_attr:
            code = result_node.attrib.get(code_attr)
            if code and code != "5000":
                return True
        if require_id_attr and not result_node.attrib.get(require_id_attr):
            return True
    if text_tag:
        result = _find_text(root, text_tag)
        if not result:
            return True
    return False


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
    result = _find_text(root, "Paquete")
    if not result:
        raise ValueError("No se encontro Paquete en la respuesta.")
    return base64.b64decode(result)


def _extract_descarga_result(xml_bytes: bytes) -> tuple[bytes | None, str | None, str | None]:
    header_code, header_message = _extract_descarga_header_status(xml_bytes)
    if header_code and header_code != "5000":
        return None, header_code, header_message or "Error en descarga."
    try:
        zip_bytes = extract_descarga_zip(xml_bytes)
        return zip_bytes, None, None
    except ValueError as exc:
        fault_code, fault_message = _extract_fault(xml_bytes)
        if fault_code or fault_message:
            return None, fault_code, fault_message
        return None, header_code, header_message or str(exc)


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


def _extract_fault(xml_text: str | bytes) -> tuple[str | None, str | None]:
    root = ET.fromstring(xml_text)
    fault = _find_node(root, "Fault")
    if fault is None:
        return None, None
    fault_code = _find_text(fault, "faultcode")
    fault_message = _find_text(fault, "faultstring")
    return fault_code, fault_message


def _extract_descarga_header_status(xml_text: str | bytes) -> tuple[str | None, str | None]:
    root = ET.fromstring(xml_text)
    header_node = _find_node(root, "respuesta")
    if header_node is None:
        return None, None
    code = header_node.attrib.get("CodEstatus")
    message = header_node.attrib.get("Mensaje")
    return code, message
