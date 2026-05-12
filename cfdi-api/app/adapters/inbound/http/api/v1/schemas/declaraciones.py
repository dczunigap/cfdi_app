from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DeclaracionListResponse(BaseModel):
    id: Optional[int]
    year: int
    month: int
    rfc: Optional[str]
    folio: Optional[str]
    fecha_presentacion: Optional[datetime]
    cantidad_a_cargo: Optional[float]
    saldo_a_favor: Optional[float]
    saldo_a_pagar: Optional[float]
    filename: Optional[str]
    original_name: Optional[str]
    num_pages: Optional[int]
    sha256: Optional[str]


class DeclaracionDetailResponse(BaseModel):
    id: Optional[int]
    year: int
    month: int
    rfc: Optional[str]
    folio: Optional[str]
    fecha_presentacion: Optional[datetime]
    cantidad_a_cargo: Optional[float]
    saldo_a_favor: Optional[float]
    saldo_a_pagar: Optional[float]
    filename: Optional[str]
    original_name: Optional[str]
    num_pages: Optional[int]
    sha256: Optional[str]
    text_excerpt: Optional[str]
