from __future__ import annotations

from typing import Protocol


class SatCrypto(Protocol):
    def encrypt_text(self, value: str | None) -> str | None:
        ...

    def decrypt_text(self, token: str | None) -> str | None:
        ...

    def encrypt_bytes(self, data: bytes) -> bytes:
        ...

    def decrypt_bytes(self, token: bytes) -> bytes:
        ...
