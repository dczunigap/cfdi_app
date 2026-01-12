from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DeclaracionPDF:
    year: int
    month: int
    rfc: Optional[str] = None
    folio: Optional[str] = None
    fecha_presentacion: Optional[datetime] = None
    sha256: Optional[str] = None
    filename: Optional[str] = None
    original_name: Optional[str] = None
    num_pages: Optional[int] = None
    text_excerpt: Optional[str] = None
    created_at: Optional[datetime] = None
