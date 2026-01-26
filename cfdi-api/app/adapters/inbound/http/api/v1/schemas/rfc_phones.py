from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RfcPhoneCreateRequest(BaseModel):
    phone: str
    rfc: str


class RfcPhoneResponse(BaseModel):
    id: Optional[int]
    phone: str
    rfc: str
