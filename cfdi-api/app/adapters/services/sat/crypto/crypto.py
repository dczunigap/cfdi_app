from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def encrypt_text(value: str | None) -> str | None:
    if not value:
        return None
    fernet = _get_fernet()
    token = fernet.encrypt(value.encode("utf-8"))
    return token.decode("ascii")


def decrypt_text(token: str | None) -> str | None:
    if not token:
        return None
    fernet = _get_fernet()
    try:
        value = fernet.decrypt(token.encode("ascii"))
        return value.decode("utf-8")
    except InvalidToken:
        return token


def encrypt_bytes(data: bytes) -> bytes:
    fernet = _get_fernet()
    return fernet.encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    fernet = _get_fernet()
    return fernet.decrypt(token)


def _get_fernet() -> Fernet:
    secret = (settings.sat_password_secret or "").strip()
    if not secret:
        raise ValueError("SAT_PASSWORD_SECRET no esta configurado.")
    try:
        return Fernet(secret.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise ValueError("SAT_PASSWORD_SECRET invalido para Fernet.") from exc
