from __future__ import annotations

from typing import Any, Protocol


class SatZipProcessor(Protocol):
    def process_zip(self, db: Any, zip_bytes: bytes) -> None:
        ...
