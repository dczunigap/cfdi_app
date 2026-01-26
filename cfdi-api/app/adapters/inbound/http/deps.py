from typing import Iterator, Optional

import re

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from app.adapters.outbound.db.session import SessionLocal
from app.core.security import get_current_user


def optional_user() -> Optional[dict]:
    return get_current_user()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_rfc(x_rfc: str | None = Header(default=None, alias="X-RFC")) -> str | None:
    value = (x_rfc or "").strip().upper()
    if not value:
        return None
    if not re.match(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$", value):
        raise HTTPException(status_code=400, detail="RFC invalido en header X-RFC")
    return value
