import sys
from pathlib import Path
import unittest
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from cryptography.x509.oid import NameOID
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import MI_RFC
from db import engine
from models import SatCredential
from sat_crypto import decrypt_password
from sat_ws_security import build_auth_envelope, load_sat_key_material_from_bytes


class TestSatAuthEnvelope(unittest.TestCase):
    def test_build_auth_envelope_contains_security_blocks(self) -> None:
        with Session(engine) as db:
            row = db.query(SatCredential).filter(SatCredential.rfc == MI_RFC).one_or_none()
            if not row:
                self.skipTest("No hay credenciales SAT en la BD para MI_RFC.")

        password = decrypt_password(row.key_password)
        material = load_sat_key_material_from_bytes(row.cert_der, row.key_der, password)
        envelope = build_auth_envelope(material)

        self.assertIn("Autentica", envelope)
        self.assertIn("BinarySecurityToken", envelope)
        self.assertIn("Signature", envelope)
        self.assertIn("Security", envelope)


if __name__ == "__main__":
    unittest.main()
