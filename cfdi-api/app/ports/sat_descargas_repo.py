from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.sat.entities import SatDescarga


class SatDescargasRepository(Protocol):
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
        ...

    def get_by_id(self, descarga_id: int) -> SatDescarga | None:
        ...

    def update(self, descarga_id: int, **fields) -> SatDescarga | None:
        ...

    def list_pending(self, now: datetime) -> list[SatDescarga]:
        ...

    def list_by_rfc(
        self,
        rfc: str,
        estado: str | None,
        limit: int,
        offset: int,
    ) -> list[SatDescarga]:
        ...

    def delete(self, descarga_id: int) -> None:
        ...
