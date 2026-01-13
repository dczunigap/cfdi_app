from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session


def apply_optional_filter(query: Select, field, value: Any) -> Select:
    if value is None or value == "":
        return query
    return query.where(field == value)


def exists_by_field(db: Session, model, field, value: Any) -> bool:
    if not value:
        return False
    return db.execute(select(model.id).where(field == value)).first() is not None
