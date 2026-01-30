from __future__ import annotations

from typing import Protocol


class SatStorage(Protocol):
    def save_zip(self, rfc: str, id_paquete: str, content: bytes) -> str:
        ...

    def open_zip(self, rfc: str, id_paquete: str) -> bytes:
        ...
