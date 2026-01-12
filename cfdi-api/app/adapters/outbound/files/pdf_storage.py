from __future__ import annotations

from pathlib import Path

from app.ports.pdf_storage import PdfStorage


class LocalPdfStorage(PdfStorage):
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, data: bytes) -> str:
        path = self._base_dir / filename
        path.write_bytes(data)
        return str(path)

    def read(self, filename: str) -> bytes:
        return (self._base_dir / filename).read_bytes()
