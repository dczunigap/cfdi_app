from __future__ import annotations

from typing import Protocol


class PdfStorage(Protocol):
    def save(self, filename: str, data: bytes) -> str:
        ...

    def read(self, filename: str) -> bytes:
        ...
