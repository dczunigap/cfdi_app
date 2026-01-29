from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import UserModel
from datetime import datetime, timezone


class SqlUserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> UserModel | None:
        return self._db.get(UserModel, user_id)

    def get_by_email(self, email: str) -> UserModel | None:
        normalized = (email or "").strip().lower()
        if not normalized:
            return None
        return (
            self._db.execute(select(UserModel).where(UserModel.email == normalized))
            .scalar_one_or_none()
        )

    def get_by_username(self, username: str) -> UserModel | None:
        normalized = (username or "").strip().lower()
        if not normalized:
            return None
        return (
            self._db.execute(select(UserModel).where(UserModel.username == normalized))
            .scalar_one_or_none()
        )

    def list_all(self) -> list[UserModel]:
        return list(self._db.execute(select(UserModel).order_by(UserModel.id)).scalars().all())

    def create(self, username: str, email: str, password_hash: str) -> UserModel:
        model = UserModel(
            username=(username or "").strip().lower(),
            email=(email or "").strip().lower(),
            password_hash=password_hash,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def update(self, model: UserModel) -> UserModel:
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def delete(self, model: UserModel) -> None:
        self._db.delete(model)
        self._db.commit()

    def update_last_login(self, model: UserModel) -> None:
        model.last_login_at = datetime.now(timezone.utc)
        self._db.commit()

    def count_users(self) -> int:
        return int(self._db.execute(select(func.count(UserModel.id))).scalar() or 0)
