from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import PlatformRfcModel


class SqlPlatformRfcRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[PlatformRfcModel]:
        return self._db.scalars(select(PlatformRfcModel).order_by(PlatformRfcModel.rfc)).all()

    def get_by_id(self, rfc_id: int) -> PlatformRfcModel | None:
        return self._db.get(PlatformRfcModel, rfc_id)

    def get_by_rfc(self, rfc: str) -> PlatformRfcModel | None:
        return (
            self._db.execute(select(PlatformRfcModel).where(PlatformRfcModel.rfc == rfc))
            .scalar_one_or_none()
        )

    def add(self, rfc: str, nombre: str | None = None) -> PlatformRfcModel:
        model = PlatformRfcModel(rfc=rfc, nombre=nombre)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def delete(self, model: PlatformRfcModel) -> None:
        self._db.delete(model)
        self._db.commit()
