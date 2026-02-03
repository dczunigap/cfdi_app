from __future__ import annotations

from datetime import datetime
from lxml import etree

from app.adapters.services.sat.soap.kind import is_retenciones_kind, normalize_sat_kind
from app.adapters.services.sat.wsse.xml_signature import sign_enveloped_element
from app.adapters.services.sat.wsse.ws_security import SOAP_ENV, SatKeyMaterial
from app.application.sat.dto import SolicitudDescargaParams

DIAG = "http://schemas.microsoft.com/2004/09/ServiceModel/Diagnostics"
ACTIVITY_ID_VALUE = "00000000-0000-0000-0000-000000000000"

DESCARGA_NS = "http://DescargaMasivaTerceros.sat.gob.mx"


def build_solicitud_descarga_envelope(
    params: SolicitudDescargaParams,
    key_material: SatKeyMaterial,
    tag_name: str = "SolicitaDescargaEmitidos",
) -> str:
    envelope = etree.Element(etree.QName(SOAP_ENV, "Envelope"), nsmap={"s": SOAP_ENV})
    header = etree.SubElement(envelope, etree.QName(SOAP_ENV, "Header"))
    activity = etree.SubElement(header, etree.QName(DIAG, "ActivityId"), nsmap={None: DIAG})
    activity.set("CorrelationId", ACTIVITY_ID_VALUE)
    activity.text = ACTIVITY_ID_VALUE
    body = etree.SubElement(
        envelope,
        etree.QName(SOAP_ENV, "Body"),
        nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance", "xsd": "http://www.w3.org/2001/XMLSchema"},
    )
    solicita = etree.SubElement(body, etree.QName(DESCARGA_NS, tag_name), nsmap={None: DESCARGA_NS})

    solicitud = etree.SubElement(
        solicita,
        etree.QName(DESCARGA_NS, "solicitud"),
        attrib=_solicitud_attribs(params),
    )
    if params.rfc_receptores:
        receptores = etree.SubElement(solicitud, etree.QName(DESCARGA_NS, "RfcReceptores"))
        for rfc in params.rfc_receptores:
            rec = etree.SubElement(receptores, etree.QName(DESCARGA_NS, "RfcReceptor"))
            rec.text = rfc

    sign_enveloped_element(solicitud, key_material.key_pem, key_material.cert_pem)
    return etree.tostring(envelope, encoding="utf-8", xml_declaration=False).decode("utf-8")


def build_verificacion_envelope(
    rfc_solicitante: str,
    id_solicitud: str,
    key_material: SatKeyMaterial,
) -> str:
    envelope = etree.Element(etree.QName(SOAP_ENV, "Envelope"), nsmap={"s": SOAP_ENV})
    header = etree.SubElement(envelope, etree.QName(SOAP_ENV, "Header"))
    activity = etree.SubElement(header, etree.QName(DIAG, "ActivityId"), nsmap={None: DIAG})
    activity.set("CorrelationId", ACTIVITY_ID_VALUE)
    activity.text = ACTIVITY_ID_VALUE
    body = etree.SubElement(
        envelope,
        etree.QName(SOAP_ENV, "Body"),
        nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance", "xsd": "http://www.w3.org/2001/XMLSchema"},
    )
    verifica = etree.SubElement(
        body, etree.QName(DESCARGA_NS, "VerificaSolicitudDescarga"), nsmap={None: DESCARGA_NS}
    )
    solicitud = etree.SubElement(
        verifica,
        etree.QName(DESCARGA_NS, "solicitud"),
        attrib={"RfcSolicitante": rfc_solicitante, "IdSolicitud": id_solicitud},
    )
    sign_enveloped_element(solicitud, key_material.key_pem, key_material.cert_pem)
    return etree.tostring(envelope, encoding="utf-8", xml_declaration=False).decode("utf-8")


def build_descarga_paquete_envelope(
    rfc_solicitante: str,
    id_paquete: str,
    key_material: SatKeyMaterial,
) -> str:
    envelope = etree.Element(etree.QName(SOAP_ENV, "Envelope"), nsmap={"s": SOAP_ENV})
    header = etree.SubElement(envelope, etree.QName(SOAP_ENV, "Header"))
    activity = etree.SubElement(header, etree.QName(DIAG, "ActivityId"), nsmap={None: DIAG})
    activity.set("CorrelationId", ACTIVITY_ID_VALUE)
    activity.text = ACTIVITY_ID_VALUE
    body = etree.SubElement(
        envelope,
        etree.QName(SOAP_ENV, "Body"),
        nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance", "xsd": "http://www.w3.org/2001/XMLSchema"},
    )
    descarga = etree.SubElement(
        body,
        etree.QName(DESCARGA_NS, "PeticionDescargaMasivaTercerosEntrada"),
        nsmap={None: DESCARGA_NS},
    )
    solicitud = etree.SubElement(
        descarga,
        etree.QName(DESCARGA_NS, "peticionDescarga"),
        attrib={"RfcSolicitante": rfc_solicitante, "IdPaquete": id_paquete},
    )
    sign_enveloped_element(solicitud, key_material.key_pem, key_material.cert_pem)
    return etree.tostring(envelope, encoding="utf-8", xml_declaration=False).decode("utf-8")


def _solicitud_attribs(params: SolicitudDescargaParams) -> dict[str, str]:
    tipo_solicitud = _normalize_tipo_solicitud(params.tipo_solicitud, params.kind)
    attrs = {
        "RfcSolicitante": params.rfc_solicitante,
        "FechaInicial": _format_dt(params.fecha_inicial),
        "FechaFinal": _format_dt(params.fecha_final),
        "TipoSolicitud": tipo_solicitud,
    }
    if params.rfc_emisor:
        attrs["RfcEmisor"] = _normalize_rfc(params.rfc_emisor)
    if params.rfc_receptor:
        attrs["RfcReceptor"] = _normalize_rfc(params.rfc_receptor)
    if params.rfc_a_cuenta_terceros is not None:
        attrs["RfcACuentaTerceros"] = _normalize_rfc(params.rfc_a_cuenta_terceros)
    else:
        attrs["RfcACuentaTerceros"] = ""
    if params.tipo_comprobante is not None:
        attrs["TipoComprobante"] = _normalize_tipo_comprobante(params.tipo_comprobante)
    else:
        attrs["TipoComprobante"] = ""
    if params.complemento:
        attrs["Complemento"] = _normalize_complemento(params.complemento)
    if params.estado_comprobante is not None:
        attrs["EstadoComprobante"] = _normalize_estado_comprobante(params.estado_comprobante)
    else:
        attrs["EstadoComprobante"] = ""
    if params.folio:
        attrs["Folio"] = params.folio
    if params.uuid:
        attrs["UUID"] = params.uuid
    return attrs


def _normalize_tipo_solicitud(value: str, kind: str) -> str:
    normalized_kind = normalize_sat_kind(kind)
    if is_retenciones_kind(kind):
        return "RETENCION"
    if normalized_kind in {"cfdi", "cfd"}:
        return "CFDI"
    normalized = (value or "").strip()
    return normalized


def _normalize_tipo_comprobante(value: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return ""
    upper = normalized.upper()
    if upper in {"I", "E", "T", "N", "P"}:
        return upper
    return normalized


def _normalize_estado_comprobante(value: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return ""
    lowered = normalized.lower()
    if lowered in {"vigente", "vigentes"}:
        return "Vigente"
    if lowered in {"cancelado", "cancelados"}:
        return "Cancelado"
    return normalized


def _normalize_complemento(value: str) -> str:
    normalized = (value or "").strip()
    return normalized


def _normalize_rfc(value: str | None) -> str:
    return (value or "").strip().upper()


def _format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S")
