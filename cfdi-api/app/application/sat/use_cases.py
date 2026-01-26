from __future__ import annotations

from app.adapters.services.sat.pkcs12.pfx import build_pfx_from_cert_key
from app.domain.sat.entities import SatCredential
from app.ports.sat_crypto import SatCrypto
from app.ports.sat_credentials_repo import SatCredentialsRepository
from app.ports.sat_gateway import SatGateway


def list_credentials(repo: SatCredentialsRepository) -> list[SatCredential]:
    return repo.list_all()


def upsert_credentials(
    repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    rfc: str,
    pfx_bytes: bytes | None,
    cert_bytes: bytes | None,
    key_bytes: bytes | None,
    key_password: str | None,
) -> SatCredential:
    if pfx_bytes and (cert_bytes or key_bytes):
        raise ValueError("Usa PFX o CER/KEY, no ambos.")
    if not key_password:
        raise ValueError("Password requerido.")
    if not pfx_bytes and (not cert_bytes or not key_bytes):
        raise ValueError("PFX o archivos .cer/.key son requeridos.")

    if not pfx_bytes:
        pfx_bytes = build_pfx_from_cert_key(cert_bytes or b"", key_bytes or b"", key_password)

    gateway.load_key_material(pfx_bytes, key_password)
    encrypted_pfx = crypto.encrypt_bytes(pfx_bytes)
    encrypted_password = crypto.encrypt_text(key_password)
    return repo.upsert(rfc, encrypted_pfx, encrypted_password)


def delete_credentials(repo: SatCredentialsRepository, rfc: str) -> None:
    repo.delete(rfc)


def authenticate(
    repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    rfc: str,
    kind: str,
    soap_action: str | None = None,
    to_url: str | None = None,
    action: str | None = None,
) -> str:
    cred = repo.get_by_rfc(rfc)
    if not cred:
        raise ValueError("RFC sin credenciales.")

    password = crypto.decrypt_text(cred.pfx_password_encrypted)
    pfx_bytes = crypto.decrypt_bytes(cred.pfx_encrypted)
    key_material = gateway.load_key_material(pfx_bytes, password)
    return gateway.autenticar(
        kind=kind,
        key_material=key_material,
        soap_action=soap_action,
        to_url=to_url,
        action=action,
    )
