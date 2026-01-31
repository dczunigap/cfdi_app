from __future__ import annotations

from pydantic import BaseModel


class UserRfcCreateRequest(BaseModel):
    user_id: int
    rfc: str


class UserRfcResponse(BaseModel):
    user_id: int
    rfc: str
