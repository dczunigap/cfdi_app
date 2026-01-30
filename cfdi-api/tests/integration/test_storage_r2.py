from __future__ import annotations

import os
import unittest
from uuid import uuid4


class TestStorageR2(unittest.TestCase):
    def setUp(self) -> None:
        if (os.getenv("SAT_STORAGE_BACKEND") or "").lower() != "r2":
            self.skipTest("SAT_STORAGE_BACKEND != r2")

        try:
            import minio  # noqa: F401
        except Exception:
            self.skipTest("minio no instalado")

        if not os.getenv("R2_ENDPOINT") or not os.getenv("R2_BUCKET"):
            self.skipTest("R2 config incompleta")

    def test_put_get_zip(self) -> None:
        from app.adapters.outbound.files.storage_factory import build_storage

        storage = build_storage()
        rfc = "AAA010101AAA"
        paquete = f"test-{uuid4()}"
        payload = b"dummy-zip-bytes"

        key = storage.save_zip(rfc, paquete, payload)
        self.assertTrue(key.endswith(f"{paquete}.zip"))
        data = storage.open_zip(rfc, paquete)
        self.assertEqual(data, payload)
