from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import UserRfcModel
from app.ports.user_rfcs_repo import UserRfcsRepository


class SqlUserRfcsRepository(UserRfcsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def is_allowed(self, user_id: int, rfc: str) -> bool:
        row = (
            self._db.execute(
                select(UserRfcModel).where(
                    UserRfcModel.user_id == user_id,
                    UserRfcModel.rfc == rfc,
                )
            )
            .scalars()
            .first()
        )
        return row is not None

    def add(self, user_id: int, rfc: str) -> None:
        row = UserRfcModel(user_id=user_id, rfc=rfc)
        self._db.add(row)
        self._db.commit()

    def remove(self, user_id: int, rfc: str) -> None:
        row = (
            self._db.execute(
                select(UserRfcModel).where(
                    UserRfcModel.user_id == user_id,
                    UserRfcModel.rfc == rfc,
                )
            )
            .scalars()
            .first()
        )
        if row:
            self._db.delete(row)
            self._db.commit()

    def list_by_user(self, user_id: int) -> list[str]:
        rows = (
            self._db.execute(select(UserRfcModel.rfc).where(UserRfcModel.user_id == user_id))
            .scalars()
            .all()
        )
        return list(rows)
