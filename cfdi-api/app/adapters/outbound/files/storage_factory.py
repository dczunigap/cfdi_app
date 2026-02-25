from __future__ import annotations

import os

from app.adapters.outbound.files.sat_storage_fs import SatStorageFs
from app.ports.sat_storage import SatStorage


def build_storage() -> SatStorage:
    backend = (os.getenv("SAT_STORAGE_BACKEND") or "fs").strip().lower()
    if backend == "r2":
        from app.adapters.outbound.r2.sat_storage_r2 import SatStorageR2
        return SatStorageR2()
    return SatStorageFs()
