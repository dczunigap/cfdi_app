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


def _normalize_rfc_value(value: str | None) -> str | None:
    normalized = (value or "").strip().upper()
    if not normalized:
        return None
    if not re.match(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$", normalized):
        raise HTTPException(status_code=400, detail="RFC invalido en header X-RFC")
    return normalized


def get_rfc(x_rfc: str | None = Header(default=None, alias="X-RFC")) -> str | None:
    return _normalize_rfc_value(x_rfc)


def get_required_rfc(x_rfc: str | None = Header(default=None, alias="X-RFC")) -> str:
    value = _normalize_rfc_value(x_rfc)
    if not value:
        raise HTTPException(status_code=400, detail="Header X-RFC requerido")
    return value
