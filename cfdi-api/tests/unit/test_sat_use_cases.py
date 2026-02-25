from __future__ import annotations

import unittest

from app.application.sat import use_cases
from app.domain.sat.entities import SatCredential


class FakeRepo:
    def __init__(self) -> None:
        self._store: dict[str, SatCredential] = {}

    def list_all(self) -> list[SatCredential]:
        return list(self._store.values())

    def get_by_rfc(self, rfc: str) -> SatCredential | None:
        return self._store.get(rfc)

    def upsert(self, rfc: str, pfx_encrypted: bytes, pfx_password_encrypted: str | None) -> SatCredential:
        cred = SatCredential(
            rfc=rfc,
            pfx_encrypted=pfx_encrypted,
            pfx_password_encrypted=pfx_password_encrypted,
            created_at=self._store.get(rfc, SatCredential(rfc, b"", None, _dt(), None)).created_at,
            updated_at=None,
        )
        self._store[rfc] = cred
        return cred

    def delete(self, rfc: str) -> None:
        self._store.pop(rfc, None)


class FakeCrypto:
    def encrypt_text(self, value: str | None) -> str | None:
        return f"enc:{value}" if value is not None else None

    def decrypt_text(self, token: str | None) -> str | None:
        if token and token.startswith("enc:"):
            return token[4:]
        return token

    def encrypt_bytes(self, data: bytes) -> bytes:
        return b"enc:" + data

    def decrypt_bytes(self, token: bytes) -> bytes:
        if token.startswith(b"enc:"):
            return token[4:]
        return token


def _dt():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


class TestSatUseCases(unittest.TestCase):
    def test_upsert_requires_inputs(self) -> None:
        repo = FakeRepo()
        crypto = FakeCrypto()
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            use_cases.upsert_credentials(repo, crypto, gateway, "AAA010101AAA", None, None, None, None)

    def test_upsert_with_pfx(self) -> None:
        repo = FakeRepo()
        crypto = FakeCrypto()
        gateway = FakeGateway()
        cred = use_cases.upsert_credentials(
            repo,
            crypto,
            gateway,
            "AAA010101AAA",
            b"pfx",
            None,
            None,
            "pwd",
        )
        self.assertEqual(cred.rfc, "AAA010101AAA")
        self.assertTrue(cred.pfx_encrypted.startswith(b"enc:"))

    def test_authenticate_missing(self) -> None:
        repo = FakeRepo()
        crypto = FakeCrypto()
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            use_cases.authenticate(repo, crypto, gateway, "AAA010101AAA", "cfdi")


class FakeGateway:
    def load_key_material(self, pfx_bytes: bytes, password: str | None):
        return object()

    def autenticar(self, kind: str, key_material, soap_action=None, to_url=None, action=None):
        return "token"


if __name__ == "__main__":
    unittest.main()
