from __future__ import annotations

from cryptography import x509
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_der_private_key,
    load_pem_private_key,
    pkcs12,
)

from app.adapters.services.sat.wsse.ws_security import SatKeyMaterial


def build_pfx_from_cert_key(cert_der: bytes, key_bytes: bytes, password: str | None) -> bytes:
    cert = _load_certificate(cert_der)
    key = _load_private_key(key_bytes, password)
    encryption = BestAvailableEncryption(password.encode("utf-8")) if password else NoEncryption()
    name = None
    try:
        name_text = cert.subject.rfc4514_string()
        if name_text:
            name = name_text.encode("utf-8", errors="ignore")
    except Exception:
        name = None
    return pkcs12.serialize_key_and_certificates(
        name=name,
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=encryption,
    )


def load_key_material_from_pfx_bytes(pfx_bytes: bytes, password: str | None) -> SatKeyMaterial:
    pass_bytes = password.encode("utf-8") if password else None
    key, cert, _cas = pkcs12.load_key_and_certificates(pfx_bytes, pass_bytes)
    if not key or not cert:
        raise ValueError("PFX sin llave privada o certificado.")
    cert_der = cert.public_bytes(Encoding.DER)
    cert_pem = cert.public_bytes(Encoding.PEM)
    key_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    return SatKeyMaterial(cert_der=cert_der, cert_pem=cert_pem, key_pem=key_pem)


def _load_private_key(key_bytes: bytes, password: str | None):
    pass_bytes = password.encode("utf-8") if password else None
    try:
        return load_der_private_key(key_bytes, password=pass_bytes)
    except ValueError:
        return load_pem_private_key(key_bytes, password=pass_bytes)


def _load_certificate(cert_bytes: bytes) -> x509.Certificate:
    try:
        return x509.load_der_x509_certificate(cert_bytes)
    except ValueError:
        return x509.load_pem_x509_certificate(cert_bytes)
