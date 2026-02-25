from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import (
    RegimenDeclaracionConfigDetalleModel,
    RegimenDeclaracionConfigModel,
    RegimenFiscalCatalogModel,
    TipoDeclaracionCatalogModel,
    UsoCfdiDeduccionCatalogModel,
)


class SqlDeclaracionConfigRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_catalogs(self) -> dict:
        tipos = (
            self._db.execute(select(TipoDeclaracionCatalogModel).order_by(TipoDeclaracionCatalogModel.clave))
            .scalars()
            .all()
        )
        regimenes = (
            self._db.execute(
                select(RegimenFiscalCatalogModel).order_by(
                    RegimenFiscalCatalogModel.clave,
                    RegimenFiscalCatalogModel.tipo_persona_clave,
                )
            )
            .scalars()
            .all()
        )
        usos = (
            self._db.execute(
                select(UsoCfdiDeduccionCatalogModel).order_by(
                    UsoCfdiDeduccionCatalogModel.tipo_declaracion_clave,
                    UsoCfdiDeduccionCatalogModel.clave,
                )
            )
            .scalars()
            .all()
        )
        return {
            "tipos_declaracion": [
                {
                    "clave": row.clave,
                    "descripcion": row.descripcion,
                    "activo": bool(row.activo),
                }
                for row in tipos
            ],
            "regimenes_fiscales": [
                {
                    "id": row.id,
                    "tipo_persona_clave": row.tipo_persona_clave,
                    "clave": row.clave,
                    "descripcion": row.descripcion,
                    "activo": bool(row.activo),
                }
                for row in regimenes
            ],
            "usos_cfdi_deduccion": [
                {
                    "clave": row.clave,
                    "descripcion": row.descripcion,
                    "tipo_declaracion_clave": row.tipo_declaracion_clave,
                    "activo": bool(row.activo),
                }
                for row in usos
            ],
        }

    def get_config(
        self,
        regimen_fiscal_clave: str,
        tipo_declaracion_clave: str,
    ) -> dict | None:
        regimen = self._db.execute(
            select(RegimenFiscalCatalogModel).where(RegimenFiscalCatalogModel.clave == regimen_fiscal_clave)
        ).scalar_one_or_none()
        if not regimen:
            return None

        base_query = select(RegimenDeclaracionConfigModel).where(
            RegimenDeclaracionConfigModel.regimen_fiscal_id == regimen.id,
            RegimenDeclaracionConfigModel.tipo_declaracion_clave == tipo_declaracion_clave,
        )

        config = self._db.execute(base_query).scalar_one_or_none()
        if not config:
            return None

        detalles = (
            self._db.execute(
                select(
                    RegimenDeclaracionConfigDetalleModel.uso_cfdi_clave,
                    UsoCfdiDeduccionCatalogModel.descripcion,
                    RegimenDeclaracionConfigDetalleModel.orden,
                )
                .select_from(RegimenDeclaracionConfigDetalleModel)
                .join(
                    UsoCfdiDeduccionCatalogModel,
                    RegimenDeclaracionConfigDetalleModel.uso_cfdi_clave == UsoCfdiDeduccionCatalogModel.clave,
                )
                .where(RegimenDeclaracionConfigDetalleModel.config_id == config.id)
                .order_by(RegimenDeclaracionConfigDetalleModel.orden, RegimenDeclaracionConfigDetalleModel.id)
            )
            .all()
        )

        return {
            "regimen_fiscal": {
                "id": regimen.id,
                "clave": regimen.clave,
                "descripcion": regimen.descripcion,
                "tipo_persona_clave": regimen.tipo_persona_clave,
            },
            "tipo_declaracion_clave": config.tipo_declaracion_clave,
            "activo": bool(config.activo),
            "incluir_acumulado_mensual_en_anual": bool(config.incluir_acumulado_mensual_en_anual),
            "usos_cfdi": [
                {
                    "clave": clave,
                    "descripcion": descripcion,
                    "orden": orden,
                }
                for clave, descripcion, orden in detalles
            ],
        }

    def upsert_config(
        self,
        *,
        regimen_fiscal_clave: str,
        tipo_declaracion_clave: str,
        activo: bool,
        incluir_acumulado_mensual_en_anual: bool,
        usos_cfdi: list[dict],
    ) -> int:
        regimen = self._db.execute(
            select(RegimenFiscalCatalogModel).where(RegimenFiscalCatalogModel.clave == regimen_fiscal_clave)
        ).scalar_one_or_none()
        if not regimen:
            raise ValueError("Regimen fiscal no encontrado")

        tipo_decl = self._db.execute(
            select(TipoDeclaracionCatalogModel).where(
                TipoDeclaracionCatalogModel.clave == tipo_declaracion_clave,
                TipoDeclaracionCatalogModel.activo.is_(True),
            )
        ).scalar_one_or_none()
        if not tipo_decl:
            raise ValueError("Tipo de declaracion no encontrado o inactivo")

        claves = [str((item or {}).get("clave") or "").strip().upper() for item in usos_cfdi]
        if not claves or any(not clave for clave in claves):
            raise ValueError("Debe proporcionar al menos una clave de uso CFDI valida")

        valid_rows = (
            self._db.execute(
                select(UsoCfdiDeduccionCatalogModel.clave).where(
                    UsoCfdiDeduccionCatalogModel.tipo_declaracion_clave == tipo_declaracion_clave,
                    UsoCfdiDeduccionCatalogModel.activo.is_(True),
                    UsoCfdiDeduccionCatalogModel.clave.in_(claves),
                )
            )
            .scalars()
            .all()
        )
        valid_set = set(valid_rows)
        for clave in claves:
            if clave not in valid_set:
                raise ValueError(f"Uso CFDI no valido para el tipo de declaracion: {clave}")

        config = self._db.execute(
            select(RegimenDeclaracionConfigModel).where(
                RegimenDeclaracionConfigModel.regimen_fiscal_id == regimen.id,
                RegimenDeclaracionConfigModel.tipo_declaracion_clave == tipo_declaracion_clave,
            )
        ).scalar_one_or_none()

        if not config:
            config = RegimenDeclaracionConfigModel(
                regimen_fiscal_id=regimen.id,
                tipo_declaracion_clave=tipo_declaracion_clave,
            )
            self._db.add(config)
            self._db.flush()

        self._db.execute(
            delete(RegimenDeclaracionConfigDetalleModel).where(
                RegimenDeclaracionConfigDetalleModel.config_id == config.id
            )
        )
        for idx, item in enumerate(usos_cfdi):
            clave = str((item or {}).get("clave") or "").strip().upper()
            orden = int((item or {}).get("orden") or (idx + 1))
            self._db.add(
                RegimenDeclaracionConfigDetalleModel(
                    config_id=config.id,
                    uso_cfdi_clave=clave,
                    orden=orden,
                )
            )

        self._db.commit()
        return int(config.id)
