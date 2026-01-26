from __future__ import annotations

import unittest

from sqlalchemy.orm import Session

from app.adapters.outbound.db.session import Base, engine
from app.adapters.outbound.db.models import SatCredentialModel
from app.adapters.services.sat.crypto.crypto import decrypt_bytes, decrypt_text
from app.adapters.services.sat.pkcs12.pfx import load_key_material_from_pfx_bytes
from app.adapters.services.sat.wsse.ws_security import build_auth_envelope
from app.core.config import settings


class TestSatAuthEnvelope(unittest.TestCase):
    def test_build_auth_envelope_contains_security_blocks(self) -> None:
        if not (settings.sat_password_secret or "").strip():
            self.skipTest("SAT_PASSWORD_SECRET no configurado.")

        Base.metadata.create_all(bind=engine)
        with Session(engine) as db:
            row = db.query(SatCredentialModel).order_by(SatCredentialModel.created_at.desc()).first()
            if not row:
                self.skipTest("No hay credenciales SAT en la BD.")

        password = decrypt_text(row.pfx_password_encrypted)
        try:
            pfx_bytes = decrypt_bytes(row.pfx_encrypted)
        except Exception:
            self.skipTest("Credenciales no cifradas con la clave actual.")
        material = load_key_material_from_pfx_bytes(pfx_bytes, password)
        envelope = build_auth_envelope(material)

        self.assertIn("Autentica", envelope)
        self.assertIn("BinarySecurityToken", envelope)
        self.assertIn("Signature", envelope)
        self.assertIn("Security", envelope)


if __name__ == "__main__":
    unittest.main()
