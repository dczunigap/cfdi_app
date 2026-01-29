from __future__ import annotations

import unittest
from unittest.mock import patch

from app.adapters.services.sat.sat_gateway import SoapSatGateway


class TestSatGateway(unittest.TestCase):
    def test_load_key_material_delegates_to_pfx_loader(self) -> None:
        gateway = SoapSatGateway()
        with patch(
            "app.adapters.services.sat.sat_gateway.load_key_material_from_pfx_bytes"
        ) as loader:
            loader.return_value = object()
            result = gateway.load_key_material(b"pfx", "pwd")
        loader.assert_called_once_with(b"pfx", "pwd")
        self.assertIs(result, loader.return_value)


if __name__ == "__main__":
    unittest.main()
