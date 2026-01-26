from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import RfcPhoneModel


class SqlRfcPhoneRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[RfcPhoneModel]:
        return self._db.scalars(select(RfcPhoneModel).order_by(RfcPhoneModel.phone)).all()

    def get_by_id(self, phone_id: int) -> RfcPhoneModel | None:
        return self._db.get(RfcPhoneModel, phone_id)

    def get_by_phone(self, phone: str) -> RfcPhoneModel | None:
        return (
            self._db.execute(select(RfcPhoneModel).where(RfcPhoneModel.phone == phone))
            .scalar_one_or_none()
        )

    def upsert(self, phone: str, rfc: str) -> RfcPhoneModel:
        existing = self.get_by_phone(phone)
        if existing:
            existing.rfc = rfc
            self._db.commit()
            self._db.refresh(existing)
            return existing
        model = RfcPhoneModel(phone=phone, rfc=rfc)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def delete(self, model: RfcPhoneModel) -> None:
        self._db.delete(model)
        self._db.commit()
