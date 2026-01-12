from typing import Iterator, Optional

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
