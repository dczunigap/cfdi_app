from typing import Iterator, Optional

import re

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import UserModel
from app.adapters.outbound.db.repositories.users import SqlUserRepository
from app.adapters.outbound.db.session import SessionLocal
from app.core.config import settings
from app.core.security import decode_access_token, parse_bearer_token


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> UserModel | None:
    token = parse_bearer_token(authorization)
    if not token:
        return None
    payload = decode_access_token(token, settings.auth_secret)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    repo = SqlUserRepository(db)
    user = repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        return None
    return user


def require_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> UserModel:
    user = get_current_user(authorization=authorization, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    return user


def require_admin(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> UserModel:
    user = get_current_user(authorization=authorization, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="No autorizado")
    if not bool(getattr(user, "is_admin", False)):
        raise HTTPException(status_code=403, detail="Permisos insuficientes")
    return user


def optional_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    return get_current_user(authorization=authorization, db=db)


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
