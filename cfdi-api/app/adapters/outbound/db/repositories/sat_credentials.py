from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import SatCredentialModel
from app.domain.sat.entities import SatCredential
from app.ports.sat_credentials_repo import SatCredentialsRepository


class SqlSatCredentialsRepository(SatCredentialsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_all(self) -> list[SatCredential]:
        rows = (
            self._db.execute(select(SatCredentialModel).order_by(SatCredentialModel.rfc.asc()))
            .scalars()
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def get_by_rfc(self, rfc: str) -> SatCredential | None:
        row = (
            self._db.execute(select(SatCredentialModel).where(SatCredentialModel.rfc == rfc))
            .scalar_one_or_none()
        )
        return self._to_entity(row) if row else None

    def upsert(self, rfc: str, pfx_encrypted: bytes, pfx_password_encrypted: str | None) -> SatCredential:
        row = (
            self._db.execute(select(SatCredentialModel).where(SatCredentialModel.rfc == rfc))
            .scalar_one_or_none()
        )
        if row:
            row.pfx_encrypted = pfx_encrypted
            row.pfx_password_encrypted = pfx_password_encrypted
        else:
            row = SatCredentialModel(
                rfc=rfc,
                pfx_encrypted=pfx_encrypted,
                pfx_password_encrypted=pfx_password_encrypted,
            )
            self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return self._to_entity(row)

    def delete(self, rfc: str) -> None:
        row = (
            self._db.execute(select(SatCredentialModel).where(SatCredentialModel.rfc == rfc))
            .scalar_one_or_none()
        )
        if row:
            self._db.delete(row)
            self._db.commit()

    @staticmethod
    def _to_entity(model: SatCredentialModel) -> SatCredential:
        return SatCredential(
            rfc=model.rfc,
            pfx_encrypted=model.pfx_encrypted,
            pfx_password_encrypted=model.pfx_password_encrypted,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
