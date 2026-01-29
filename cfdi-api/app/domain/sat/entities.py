from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SatCredential:
    rfc: str
    pfx_encrypted: bytes
    pfx_password_encrypted: str | None
    created_at: datetime
    updated_at: datetime | None
