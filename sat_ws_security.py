from __future__ import annotations

import base64
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_der_private_key,
    load_pem_private_key,
)
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from lxml import etree

SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
WSU = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
DS = "http://www.w3.org/2000/09/xmldsig#"
DIAG = "http://schemas.microsoft.com/2004/09/ServiceModel/Diagnostics"
ACTIVITY_ID_VALUE = "00000000-0000-0000-0000-000000000000"
WSA_NONE = "http://schemas.microsoft.com/ws/2005/05/addressing/none"
AUTH_NS = "http://DescargaMasivaTerceros.gob.mx"
logger = logging.getLogger("cfdi_app")
_LAST_DEBUG_NOTE: str | None = None


@dataclass(frozen=True)
class SatKeyMaterial:
    cert_der: bytes
    cert_pem: bytes
    key_pem: bytes


def load_sat_key_material(cert_path: str, key_path: str, key_password: str | None) -> SatKeyMaterial:
    cert_der = Path(cert_path).read_bytes()
    cert = x509.load_der_x509_certificate(cert_der)
    cert_pem = cert.public_bytes(Encoding.PEM)
    key_der = Path(key_path).read_bytes()
    password_bytes = key_password.encode("utf-8") if key_password else None
    try:
        key = load_der_private_key(key_der, password=password_bytes)
    except ValueError:
        key = load_pem_private_key(key_der, password=password_bytes)
    key_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    return SatKeyMaterial(cert_der=cert_der, cert_pem=cert_pem, key_pem=key_pem)


def load_sat_key_material_from_bytes(
    cert_der: bytes, key_der: bytes, key_password: str | None
) -> SatKeyMaterial:
    cert = x509.load_der_x509_certificate(cert_der)
    cert_pem = cert.public_bytes(Encoding.PEM)
    password_bytes = key_password.encode("utf-8") if key_password else None
    try:
        key = load_der_private_key(key_der, password=password_bytes)
    except ValueError:
        key = load_pem_private_key(key_der, password=password_bytes)
    _validate_key_matches_cert(cert, key)
    key_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    return SatKeyMaterial(cert_der=cert_der, cert_pem=cert_pem, key_pem=key_pem)


def build_auth_envelope(
    key_material: SatKeyMaterial,
    created: datetime | None = None,
    expires: datetime | None = None,
    to_url: str | None = None,
    action: str | None = None,
    include_activity_id: bool = True,
    include_wsa: bool = False,
) -> str:
    created_dt = created or datetime.now(timezone.utc)
    created_dt = _normalize_timestamp(created_dt)
    expires_dt = expires or (created_dt + timedelta(minutes=5))
    expires_dt = _normalize_timestamp(expires_dt)
    _validate_timestamp_window(created_dt, expires_dt)
    header, security, timestamp, token_id = _build_wsse_header(
        key_material=key_material,
        created=created_dt,
        expires=expires_dt,
        to_url=to_url,
        action=action,
        include_activity_id=include_activity_id,
        include_wsa=include_wsa,
    )
    envelope = etree.Element(
        etree.QName(SOAP_ENV, "Envelope"),
        nsmap={"s": SOAP_ENV, "u": WSU},
    )
    envelope.append(header)
    signature = _sign_timestamp(timestamp, key_material.key_pem, token_id)
    security.append(signature)
    body = etree.SubElement(envelope, etree.QName(SOAP_ENV, "Body"))
    etree.SubElement(body, etree.QName(AUTH_NS, "Autentica"), nsmap={None: AUTH_NS})
    xml_text = etree.tostring(envelope, encoding="utf-8", xml_declaration=False).decode("utf-8")
    logger.debug(
        "SAT auth envelope generado len=%s cert_len=%s key_len=%s",
        len(xml_text),
        len(key_material.cert_der),
        len(key_material.key_pem),
    )
    return xml_text


def _build_wsse_header(
    key_material: SatKeyMaterial,
    created: datetime,
    expires: datetime,
    to_url: str | None,
    action: str | None,
    include_activity_id: bool,
    include_wsa: bool,
) -> tuple[etree._Element, etree._Element, etree._Element, str]:
    header = etree.Element(etree.QName(SOAP_ENV, "Header"))
    if include_activity_id:
        activity = etree.SubElement(header, etree.QName(DIAG, "ActivityId"), nsmap={None: DIAG})
        activity.set("CorrelationId", ACTIVITY_ID_VALUE)
        activity.text = ACTIVITY_ID_VALUE
    security = etree.SubElement(
        header,
        etree.QName(WSSE, "Security"),
        attrib={etree.QName(SOAP_ENV, "mustUnderstand"): "1"},
        nsmap={"o": WSSE},
    )

    timestamp_id = "_0"
    token_id = f"uuid-{uuid.uuid4()}"
    timestamp = etree.SubElement(
        security, etree.QName(WSU, "Timestamp"), attrib={etree.QName(WSU, "Id"): timestamp_id}
    )
    created_el = etree.SubElement(timestamp, etree.QName(WSU, "Created"))
    created_el.text = _format_timestamp(created)
    expires_el = etree.SubElement(timestamp, etree.QName(WSU, "Expires"))
    expires_el.text = _format_timestamp(expires)

    binary_token = etree.SubElement(
        security,
        etree.QName(WSSE, "BinarySecurityToken"),
        attrib={
            etree.QName(WSU, "Id"): token_id,
            "ValueType": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3",
            "EncodingType": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary",
        },
    )
    binary_token.text = base64.b64encode(key_material.cert_der).decode("ascii")

    if include_wsa and to_url:
        to_el = etree.SubElement(
            header,
            etree.QName(WSA_NONE, "To"),
            attrib={etree.QName(SOAP_ENV, "mustUnderstand"): "1"},
        )
        to_el.text = to_url
    if include_wsa and action:
        action_el = etree.SubElement(
            header,
            etree.QName(WSA_NONE, "Action"),
            attrib={etree.QName(SOAP_ENV, "mustUnderstand"): "1"},
        )
        action_el.text = action

    return header, security, timestamp, token_id


def _sign_timestamp(timestamp: etree._Element, key_pem: bytes, token_id: str) -> etree._Element:
    digest_value = _digest_c14n(timestamp)
    signature = etree.Element(etree.QName(DS, "Signature"), nsmap={None: DS})
    signed_info = etree.SubElement(signature, etree.QName(DS, "SignedInfo"))
    etree.SubElement(
        signed_info,
        etree.QName(DS, "CanonicalizationMethod"),
        Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    etree.SubElement(
        signed_info,
        etree.QName(DS, "SignatureMethod"),
        Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1",
    )
    timestamp_ref = timestamp.get(f"{{{WSU}}}Id")
    reference = etree.SubElement(
        signed_info, etree.QName(DS, "Reference"), URI=f"#{timestamp_ref}"
    )
    transforms = etree.SubElement(reference, etree.QName(DS, "Transforms"))
    etree.SubElement(
        transforms,
        etree.QName(DS, "Transform"),
        Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
    )
    etree.SubElement(
        reference,
        etree.QName(DS, "DigestMethod"),
        Algorithm="http://www.w3.org/2000/09/xmldsig#sha1",
    )
    digest_el = etree.SubElement(reference, etree.QName(DS, "DigestValue"))
    digest_el.text = digest_value

    signed_info_c14n = etree.tostring(signed_info, method="c14n", exclusive=True, with_comments=False)
    private_key = load_pem_private_key(key_pem, password=None)
    signature_value = private_key.sign(
        signed_info_c14n, padding.PKCS1v15(), hashes.SHA1()
    )
    sig_value_el = etree.SubElement(signature, etree.QName(DS, "SignatureValue"))
    sig_value_el.text = base64.b64encode(signature_value).decode("ascii")
    key_info = etree.SubElement(signature, etree.QName(DS, "KeyInfo"))
    str_el = etree.SubElement(key_info, etree.QName(WSSE, "SecurityTokenReference"))
    etree.SubElement(
        str_el,
        etree.QName(WSSE, "Reference"),
        ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3",
        URI=f"#{token_id}",
    )
    return signature


def _digest_c14n(element: etree._Element) -> str:
    data = etree.tostring(element, method="c14n", exclusive=True, with_comments=False)
    digest = hashes.Hash(hashes.SHA1())
    digest.update(data)
    return base64.b64encode(digest.finalize()).decode("ascii")


def _validate_key_matches_cert(cert: x509.Certificate, key) -> None:
    try:
        data = b"sat-verify"
        signature = key.sign(data, asym_padding.PKCS1v15(), hashes.SHA256())
        cert.public_key().verify(signature, data, asym_padding.PKCS1v15(), hashes.SHA256())
        logger.debug("SAT credenciales: .cer y .key coinciden.")
        _set_debug_note("SAT credenciales: .cer y .key coinciden.")
    except Exception as exc:
        logger.debug("SAT credenciales: .cer y .key NO coinciden.")
        _set_debug_note("SAT credenciales: .cer y .key NO coinciden.")
        raise ValueError("La llave privada no corresponde con el certificado (.cer).") from exc


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_timestamp_window(created: datetime, expires: datetime) -> None:
    now = datetime.now(timezone.utc)
    local_now = datetime.now()
    logger.debug(
        "SAT timestamp: local=%s utc=%s created=%s expires=%s",
        local_now.strftime("%Y-%m-%dT%H:%M:%S"),
        _format_timestamp(now),
        _format_timestamp(created),
        _format_timestamp(expires),
    )
    _append_debug_note(
        "SAT timestamp: local={local} utc={utc} created={created} expires={expires}".format(
            local=local_now.strftime("%Y-%m-%dT%H:%M:%S"),
            utc=_format_timestamp(now),
            created=_format_timestamp(created),
            expires=_format_timestamp(expires),
        )
    )
    if created > expires:
        raise ValueError("Timestamp Created mayor que Expires.")
    if expires - created > timedelta(minutes=10):
        raise ValueError("Ventana de timestamp demasiado grande.")
    skew = abs((now - created).total_seconds())
    logger.debug("SAT timestamp: skew_segundos=%s (no hay hora servidor en esta etapa).", int(skew))
    _append_debug_note(f"SAT timestamp: skew_segundos={int(skew)} (no hay hora servidor en esta etapa).")
    if skew > 300:
        raise ValueError("Timestamp fuera de rango. Verifica la hora del sistema.")


def pop_debug_note() -> str:
    global _LAST_DEBUG_NOTE
    note = _LAST_DEBUG_NOTE or ""
    _LAST_DEBUG_NOTE = None
    return note


def _set_debug_note(note: str) -> None:
    global _LAST_DEBUG_NOTE
    _LAST_DEBUG_NOTE = note


def _append_debug_note(note: str) -> None:
    global _LAST_DEBUG_NOTE
    if _LAST_DEBUG_NOTE:
        _LAST_DEBUG_NOTE = _LAST_DEBUG_NOTE + "\n" + note
    else:
        _LAST_DEBUG_NOTE = note


def _format_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
