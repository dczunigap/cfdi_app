from __future__ import annotations

from typing import Protocol

from app.domain.sat.entities import SatCredential


class SatCredentialsRepository(Protocol):
    def list_all(self) -> list[SatCredential]:
        ...

    def get_by_rfc(self, rfc: str) -> SatCredential | None:
        ...

    def upsert(self, rfc: str, pfx_encrypted: bytes, pfx_password_encrypted: str | None) -> SatCredential:
        ...

    def delete(self, rfc: str) -> None:
        ...
