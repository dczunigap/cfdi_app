from __future__ import annotations

import os
from pathlib import Path

from app.core.config import settings
from app.ports.sat_storage import SatStorage


class SatStorageFs(SatStorage):
    def __init__(self, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir or settings.sat_download_dir)

    def save_zip(self, rfc: str, id_paquete: str, content: bytes) -> str:
        rfc_dir = self._base_dir / rfc
        rfc_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{id_paquete}.zip"
        path = rfc_dir / filename
        path.write_bytes(content)
        return str(path)

    def open_zip(self, rfc: str, id_paquete: str) -> bytes:
        path = Path(self._base_dir) / rfc / f"{id_paquete}.zip"
        if not path.exists():
            raise FileNotFoundError(f"ZIP no encontrado: {path}")
        return path.read_bytes()
