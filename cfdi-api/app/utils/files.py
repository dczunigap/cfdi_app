from __future__ import annotations

import hashlib
from typing import Optional


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_pdf_filename(sha: str, original: Optional[str] = None) -> str:
    _ = original
    return f"{sha}.pdf"
