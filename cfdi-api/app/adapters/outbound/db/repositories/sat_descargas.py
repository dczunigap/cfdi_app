from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.adapters.outbound.db.models import SatDescargaModel
from app.domain.sat.entities import SatDescarga
from app.ports.sat_descargas_repo import SatDescargasRepository


class SqlSatDescargasRepository(SatDescargasRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        rfc: str,
        kind: str,
        tipo_solicitud: str,
        anio_filtro: int | None,
        mes_filtro: int | None,
        id_solicitud: str | None,
        estado: str,
        codigo_estado: str | None,
        mensaje_estado: str | None,
        paquetes: list[str],
        link_descarga: str | None,
        zip_path: str | None,
        attempts: int,
        next_check_at: datetime | None,
    ) -> SatDescarga:
        row = SatDescargaModel(
            rfc=rfc,
            kind=kind,
            tipo_solicitud=tipo_solicitud,
            anio_filtro=anio_filtro,
            mes_filtro=mes_filtro,
            id_solicitud=id_solicitud,
            estado=estado,
            codigo_estado=codigo_estado,
            mensaje_estado=mensaje_estado,
            paquetes=paquetes,
            link_descarga=link_descarga,
            zip_path=zip_path,
            attempts=attempts,
            next_check_at=next_check_at,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return self._to_entity(row)

    def get_by_id(self, descarga_id: int) -> SatDescarga | None:
        row = self._db.get(SatDescargaModel, descarga_id)
        return self._to_entity(row) if row else None

    def update(self, descarga_id: int, **fields) -> SatDescarga | None:
        row = self._db.get(SatDescargaModel, descarga_id)
        if not row:
            return None
        for key, value in fields.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self._db.commit()
        self._db.refresh(row)
        return self._to_entity(row)

    def list_pending(self, now: datetime) -> list[SatDescarga]:
        rows = (
            self._db.execute(
                select(SatDescargaModel)
                .where(SatDescargaModel.estado.in_(["SOLICITADA", "EN_PROCESO", "LISTA"]))
                .where(or_(SatDescargaModel.next_check_at.is_(None), SatDescargaModel.next_check_at <= now))
                .order_by(SatDescargaModel.next_check_at.asc().nullsfirst(), SatDescargaModel.id.asc())
            )
            .scalars()
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def list_by_rfc(
        self,
        rfc: str,
        estado: str | None,
        limit: int,
        offset: int,
    ) -> list[SatDescarga]:
        query = select(SatDescargaModel).where(SatDescargaModel.rfc == rfc)
        if estado:
            query = query.where(SatDescargaModel.estado == estado)
        rows = (
            self._db.execute(
                query.order_by(SatDescargaModel.created_at.desc(), SatDescargaModel.id.desc())
                .offset(offset)
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def delete(self, descarga_id: int) -> None:
        row = self._db.get(SatDescargaModel, descarga_id)
        if not row:
            return
        self._db.delete(row)
        self._db.commit()

    @staticmethod
    def _to_entity(model: SatDescargaModel) -> SatDescarga:
        return SatDescarga(
            id=model.id,
            rfc=model.rfc,
            kind=model.kind,
            tipo_solicitud=model.tipo_solicitud,
            anio_filtro=model.anio_filtro,
            mes_filtro=model.mes_filtro,
            id_solicitud=model.id_solicitud,
            estado=model.estado,
            codigo_estado=model.codigo_estado,
            mensaje_estado=model.mensaje_estado,
            paquetes=list(model.paquetes or []),
            link_descarga=model.link_descarga,
            zip_path=model.zip_path,
            attempts=int(model.attempts or 0),
            next_check_at=model.next_check_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
