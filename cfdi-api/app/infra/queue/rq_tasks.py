from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.adapters.outbound.db.session import SessionLocal
from app.adapters.outbound.db.repositories.sat_credentials import SqlSatCredentialsRepository
from app.adapters.outbound.db.repositories.sat_descargas import SqlSatDescargasRepository
from app.adapters.outbound.files.sat_storage_fs import SatStorageFs
from app.adapters.services.sat.crypto.crypto_service import FernetSatCrypto
from app.adapters.services.sat.gateway_factory import build_sat_gateway
from app.application.sat.descargas_service import (
    STATUS_EN_PROCESO,
    STATUS_LISTA,
    descargar_y_procesar,
    verificar_descarga,
)
from app.infra.queue.rq_conn import get_queue


def verificar_descarga_job(descarga_id: int, schedule_next: bool = True) -> None:
    with SessionLocal() as db:
        repo = SqlSatDescargasRepository(db)
        cred_repo = SqlSatCredentialsRepository(db)
        crypto = FernetSatCrypto()
        gateway = build_sat_gateway()

        descarga = verificar_descarga(
            repo=repo,
            cred_repo=cred_repo,
            crypto=crypto,
            gateway=gateway,
            descarga_id=descarga_id,
        )
        if not descarga:
            return

        q = get_queue()
        if not schedule_next:
            return
        if descarga.estado == STATUS_EN_PROCESO and descarga.next_check_at:
            delay = max(0, int((descarga.next_check_at - datetime.now(timezone.utc)).total_seconds()))
            q.enqueue_in(timedelta(seconds=delay), verificar_descarga_job, descarga.id)
        elif descarga.estado == STATUS_LISTA:
            q.enqueue(descargar_paquetes_job, descarga.id)


def descargar_paquetes_job(descarga_id: int) -> None:
    with SessionLocal() as db:
        repo = SqlSatDescargasRepository(db)
        cred_repo = SqlSatCredentialsRepository(db)
        crypto = FernetSatCrypto()
        gateway = build_sat_gateway()
        storage = SatStorageFs()

        descargar_y_procesar(
            repo=repo,
            cred_repo=cred_repo,
            crypto=crypto,
            gateway=gateway,
            storage=storage,
            db=db,
            descarga_id=descarga_id,
        )
