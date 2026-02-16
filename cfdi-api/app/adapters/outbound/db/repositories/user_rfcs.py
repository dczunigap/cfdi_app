from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import (
    RfcModel,
    RegimenFiscalCatalogModel,
    TipoPersonaCatalogModel,
    UserRfcModel,
)
from app.ports.user_rfcs_repo import UserRfcsRepository


class SqlUserRfcsRepository(UserRfcsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def infer_tipo_persona_clave(rfc: str) -> str:
        rfc_value = (rfc or "").strip().upper()
        if rfc_value == "XEXX010101000":
            return "EXT"
        if len(rfc_value) == 12:
            return "PM"
        if len(rfc_value) == 13:
            return "PF"
        raise ValueError("RFC invalido para clasificar tipo de persona")

    def _get_rfc_row(self, rfc: str) -> RfcModel | None:
        return self._db.execute(select(RfcModel).where(RfcModel.rfc == rfc)).scalar_one_or_none()

    def _get_regimen(self, tipo_persona_clave: str, regimen_fiscal_clave: str) -> RegimenFiscalCatalogModel | None:
        return self._db.execute(
            select(RegimenFiscalCatalogModel).where(
                RegimenFiscalCatalogModel.tipo_persona_clave == tipo_persona_clave,
                RegimenFiscalCatalogModel.clave == regimen_fiscal_clave,
                RegimenFiscalCatalogModel.activo.is_(True),
            )
        ).scalar_one_or_none()

    def is_allowed(self, user_id: int, rfc: str) -> bool:
        row_id = (
            self._db.execute(
                select(UserRfcModel.id)
                .join(RfcModel, UserRfcModel.rfc_id == RfcModel.id)
                .where(
                    UserRfcModel.user_id == user_id,
                    RfcModel.rfc == rfc,
                )
            )
            .scalar_one_or_none()
        )
        return row_id is not None

    def add(self, user_id: int, rfc: str, regimen_fiscal_clave: str) -> None:
        tipo_persona_clave = self.infer_tipo_persona_clave(rfc)
        if not (regimen_fiscal_clave or "").strip():
            raise ValueError("regimen_fiscal_clave es requerido")

        regimen = self._get_regimen(tipo_persona_clave, regimen_fiscal_clave)
        if regimen is None:
            raise ValueError("Regimen fiscal no permitido para el tipo de persona del RFC")

        rfc_row = self._get_rfc_row(rfc)
        if rfc_row is None:
            rfc_row = RfcModel(
                rfc=rfc,
                regimen_fiscal_id=regimen.id,
            )
            self._db.add(rfc_row)
            self._db.flush()
        else:
            rfc_row.regimen_fiscal_id = regimen.id

        row = UserRfcModel(user_id=user_id, rfc_id=rfc_row.id)
        self._db.add(row)
        self._db.commit()

    def remove(self, user_id: int, rfc: str) -> None:
        row_id = (
            self._db.execute(
                select(UserRfcModel.id)
                .join(RfcModel, UserRfcModel.rfc_id == RfcModel.id)
                .where(
                    UserRfcModel.user_id == user_id,
                    RfcModel.rfc == rfc,
                )
            )
            .scalar_one_or_none()
        )
        if row_id is not None:
            self._db.execute(delete(UserRfcModel).where(UserRfcModel.id == row_id))
            self._db.commit()

    def list_by_user(self, user_id: int) -> list[dict]:
        rows = (
            self._db.execute(
                select(
                    RfcModel.rfc,
                    RegimenFiscalCatalogModel.tipo_persona_clave,
                    RegimenFiscalCatalogModel.clave,
                    RegimenFiscalCatalogModel.descripcion,
                )
                .select_from(UserRfcModel)
                .join(RfcModel, UserRfcModel.rfc_id == RfcModel.id)
                .join(RegimenFiscalCatalogModel, RfcModel.regimen_fiscal_id == RegimenFiscalCatalogModel.id)
                .where(UserRfcModel.user_id == user_id)
            )
            .all()
        )
        return [
            {
                "rfc": rfc,
                "tipo_persona_clave": tipo_persona_clave,
                "regimen_fiscal_clave": regimen_fiscal_clave,
                "regimen_fiscal_descripcion": regimen_fiscal_descripcion,
            }
            for rfc, tipo_persona_clave, regimen_fiscal_clave, regimen_fiscal_descripcion in rows
        ]

    def list_catalogs(self) -> dict:
        tipos = (
            self._db.execute(select(TipoPersonaCatalogModel).order_by(TipoPersonaCatalogModel.clave))
            .scalars()
            .all()
        )
        regimenes = (
            self._db.execute(
                select(RegimenFiscalCatalogModel).order_by(
                    RegimenFiscalCatalogModel.tipo_persona_clave,
                    RegimenFiscalCatalogModel.clave,
                )
            )
            .scalars()
            .all()
        )
        return {
            "tipos_persona": [{"clave": row.clave, "descripcion": row.descripcion} for row in tipos],
            "regimenes_fiscales": [
                {
                    "id": row.id,
                    "tipo_persona_clave": row.tipo_persona_clave,
                    "clave": row.clave,
                    "descripcion": row.descripcion,
                    "activo": row.activo,
                }
                for row in regimenes
            ],
        }
