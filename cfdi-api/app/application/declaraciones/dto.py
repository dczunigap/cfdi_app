from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DeclaracionListItem:
    id: Optional[int]
    year: int
    month: int
    rfc: Optional[str]
    folio: Optional[str]
    fecha_presentacion: Optional[datetime]
    filename: Optional[str]
    original_name: Optional[str]
    num_pages: Optional[int]
    sha256: Optional[str]


@dataclass
class DeclaracionDetail:
    id: Optional[int]
    year: int
    month: int
    rfc: Optional[str]
    folio: Optional[str]
    fecha_presentacion: Optional[datetime]
    filename: Optional[str]
    original_name: Optional[str]
    num_pages: Optional[int]
    sha256: Optional[str]
    text_excerpt: Optional[str]
