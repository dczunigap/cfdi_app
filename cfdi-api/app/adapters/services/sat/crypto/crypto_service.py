from __future__ import annotations

from app.adapters.services.sat.crypto import crypto
from app.ports.sat_crypto import SatCrypto


class FernetSatCrypto(SatCrypto):
    def encrypt_text(self, value: str | None) -> str | None:
        return crypto.encrypt_text(value)

    def decrypt_text(self, token: str | None) -> str | None:
        return crypto.decrypt_text(token)

    def encrypt_bytes(self, data: bytes) -> bytes:
        return crypto.encrypt_bytes(data)

    def decrypt_bytes(self, token: bytes) -> bytes:
        return crypto.decrypt_bytes(token)
