from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from config import SAT_PASSWORD_SECRET


def encrypt_password(password: str | None) -> str | None:
    if not password:
        return None
    fernet = _get_fernet()
    token = fernet.encrypt(password.encode("utf-8"))
    return token.decode("ascii")


def decrypt_password(token: str | None) -> str | None:
    if not token:
        return None
    fernet = _get_fernet()
    try:
        value = fernet.decrypt(token.encode("ascii"))
        return value.decode("utf-8")
    except InvalidToken:
        # Fallback for legacy plaintext values.
        return token


def _get_fernet() -> Fernet:
    if not SAT_PASSWORD_SECRET:
        raise ValueError("SAT_PASSWORD_SECRET no esta configurado.")
    try:
        return Fernet(SAT_PASSWORD_SECRET.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise ValueError("SAT_PASSWORD_SECRET invalido para Fernet.") from exc
