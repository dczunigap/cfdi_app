from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class SatCredentialResponse(BaseModel):
    rfc: str
    created_at: datetime
    updated_at: datetime | None = None
    has_password: bool
    has_pfx: bool


class SatAuthRequest(BaseModel):
    kind: str = "cfdi"
    soap_action: str | None = None
    to_url: str | None = None
    action: str | None = None
