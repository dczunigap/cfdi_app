from __future__ import annotations

import os

from app.adapters.services.sat.mock_gateway import MockSatGateway
from app.adapters.services.sat.sat_gateway import SoapSatGateway
from app.ports.sat_gateway import SatGateway


def build_sat_gateway() -> SatGateway:
    mode = (os.getenv("SAT_GATEWAY_MODE") or "soap").strip().lower()
    if mode == "mock":
        return MockSatGateway()
    return SoapSatGateway()
