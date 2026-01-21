from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PlatformRfcCreateRequest(BaseModel):
    rfc: str
    nombre: Optional[str] = None


class PlatformRfcResponse(BaseModel):
    id: Optional[int]
    rfc: str
    nombre: Optional[str] = None
