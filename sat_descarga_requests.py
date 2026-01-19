from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from lxml import etree

from sat_xml_signature import sign_enveloped_element
from sat_ws_security import SOAP_ENV, SatKeyMaterial

DIAG = "http://schemas.microsoft.com/2004/09/ServiceModel/Diagnostics"
ACTIVITY_ID_VALUE = "00000000-0000-0000-0000-000000000000"

DESCARGA_NS = "http://DescargaMasivaTerceros.sat.gob.mx"


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


def build_descarga_paquete_envelope(rfc_solicitante: str, id_paquete: str) -> str:
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
        body, etree.QName(DESCARGA_NS, "DescargaMasiva"), nsmap={None: DESCARGA_NS}
    )
    etree.SubElement(
        descarga,
        etree.QName(DESCARGA_NS, "peticionDescarga"),
        attrib={"RfcSolicitante": rfc_solicitante, "IdPaquete": id_paquete},
    )
    return etree.tostring(envelope, encoding="utf-8", xml_declaration=False).decode("utf-8")


def _solicitud_attribs(params: SolicitudDescargaParams) -> dict[str, str]:
    attrs = {
        "RfcSolicitante": params.rfc_solicitante,
        "FechaInicial": _format_dt(params.fecha_inicial),
        "FechaFinal": _format_dt(params.fecha_final),
        "TipoSolicitud": params.tipo_solicitud,
    }
    if params.rfc_emisor:
        attrs["RfcEmisor"] = params.rfc_emisor
    if params.rfc_receptor:
        attrs["RfcReceptor"] = params.rfc_receptor
    if params.rfc_a_cuenta_terceros is not None:
        attrs["RfcACuentaTerceros"] = params.rfc_a_cuenta_terceros
    else:
        attrs["RfcACuentaTerceros"] = ""
    if params.tipo_comprobante is not None:
        attrs["TipoComprobante"] = params.tipo_comprobante
    else:
        attrs["TipoComprobante"] = ""
    if params.complemento:
        attrs["Complemento"] = params.complemento
    if params.estado_comprobante is not None:
        attrs["EstadoComprobante"] = params.estado_comprobante
    else:
        attrs["EstadoComprobante"] = ""
    if params.folio:
        attrs["Folio"] = params.folio
    if params.uuid:
        attrs["UUID"] = params.uuid
    return attrs


def _format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S")
