from __future__ import annotations

import os
import socket
import shutil
import time
import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.outbound.db.session import Base, SessionLocal
from app.adapters.outbound.db.repositories.sat_credentials import SqlSatCredentialsRepository
from app.adapters.outbound.db.repositories.sat_descargas import SqlSatDescargasRepository
from app.adapters.outbound.files.sat_storage_fs import SatStorageFs
from app.adapters.services.parsers.sat_zip_processor import LocalSatZipProcessor
from app.adapters.services.sat.crypto.crypto_service import FernetSatCrypto
from app.adapters.services.sat.gateway_factory import build_sat_gateway
from app.application.sat.descargas_service import (
    STATUS_EN_PROCESO,
    STATUS_ERROR,
    STATUS_EXPIRADA,
    STATUS_LISTA,
    STATUS_SIN_RESULTADOS,
    crear_solicitud_descarga,
    descargar_y_procesar,
    verificar_descarga,
)
from app.application.sat.dto import SolicitudDescargaParams
from app.core.config import settings


class TestSatSolicitudIntegration(unittest.TestCase):
    def setUp(self) -> None:
        if (os.getenv("SAT_GATEWAY_MODE") or "").lower() == "mock":
            engine = create_engine(
                "sqlite://",
                future=True,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            Base.metadata.create_all(bind=engine)
            self._session_local = sessionmaker(
                bind=engine, autoflush=False, autocommit=False, future=True
            )
            base_dir = os.path.join(os.getcwd(), ".tmp", "sat_downloads")
            os.makedirs(base_dir, exist_ok=True)
            self._tmpdir = base_dir
            os.environ["SAT_DOWNLOAD_DIR"] = base_dir
        else:
            self._session_local = SessionLocal
            self._tmpdir = None

    def tearDown(self) -> None:
        if self._tmpdir and (os.getenv("SAT_GATEWAY_MODE") or "").lower() == "mock":
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _ensure_ready(self) -> None:
        if os.getenv("RUN_SAT_INTEGRATION") != "1":
            self.skipTest("Set RUN_SAT_INTEGRATION=1 to run SAT integration tests.")

        if not (settings.sat_password_secret or "").strip():
            self.skipTest("SAT_PASSWORD_SECRET no configurado.")

        if (os.getenv("SAT_GATEWAY_MODE") or "").lower() != "mock":
            try:
                socket.getaddrinfo("cu1-cfd-uat-webc-dmtsoli.cloudapp.net", 443)
            except Exception:
                self.skipTest("DNS no resuelve endpoints UAT del SAT.")

        with self._session_local() as db:
            repo = SqlSatCredentialsRepository(db)
            if not repo.list_all():
                if (os.getenv("SAT_GATEWAY_MODE") or "").lower() == "mock":
                    crypto = FernetSatCrypto()
                    repo.upsert(
                        rfc="AAA010101AAA",
                        pfx_encrypted=crypto.encrypt_bytes(b"mock-pfx"),
                        pfx_password_encrypted=crypto.encrypt_text("mock-pass"),
                    )
                else:
                    self.skipTest("No hay credenciales SAT en la BD.")

    def _poll_until_ready(self, descarga_id: int, max_wait_seconds: int = 900) -> str:
        start = time.time()
        with self._session_local() as db:
            repo = SqlSatDescargasRepository(db)
            cred_repo = SqlSatCredentialsRepository(db)
            crypto = FernetSatCrypto()
            gateway = build_sat_gateway()

            while time.time() - start < max_wait_seconds:
                descarga = verificar_descarga(
                    repo=repo,
                    cred_repo=cred_repo,
                    crypto=crypto,
                    gateway=gateway,
                    descarga_id=descarga_id,
                )
                if not descarga:
                    return STATUS_ERROR

                if descarga.estado in {
                    STATUS_LISTA,
                    STATUS_SIN_RESULTADOS,
                    STATUS_EXPIRADA,
                    STATUS_ERROR,
                }:
                    return descarga.estado

                time.sleep(30)
        return STATUS_ERROR

    def test_solicitud_descarga_emitidos_y_recibidos(self) -> None:
        self._ensure_ready()

        with self._session_local() as db:
            cred_repo = SqlSatCredentialsRepository(db)
            cred = cred_repo.list_all()[0]
            rfc_value = cred.rfc

            repo = SqlSatDescargasRepository(db)
            crypto = FernetSatCrypto()
            gateway = build_sat_gateway()

            params_emitidos = SolicitudDescargaParams(
                rfc_solicitante=rfc_value,
                rfc_emisor=rfc_value,
                fecha_inicial=datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc),
                fecha_final=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                tipo_solicitud="emitidos",
                tipo_descarga="CFDI",
                complemento="",
                estado_comprobante="Vigente",
                tipo_comprobante="",
                rfc_a_cuenta_terceros="",
            )
            descarga_emitidos = crear_solicitud_descarga(
                repo=repo,
                cred_repo=cred_repo,
                crypto=crypto,
                gateway=gateway,
                rfc=rfc_value,
                kind="cfdi",
                params=params_emitidos,
                tag_name="SolicitaDescargaEmitidos",
            )
            print(f"\nIdSolicitud emitidos: {descarga_emitidos.id_solicitud}")

        estado_emitidos = self._poll_until_ready(descarga_emitidos.id)
        self.assertNotEqual(estado_emitidos, STATUS_ERROR)

        if estado_emitidos == STATUS_LISTA:
            with self._session_local() as db:
                repo = SqlSatDescargasRepository(db)
                cred_repo = SqlSatCredentialsRepository(db)
                crypto = FernetSatCrypto()
                gateway = build_sat_gateway()
                storage = SatStorageFs()
                zip_processor = LocalSatZipProcessor()
                descargar_y_procesar(
                    repo=repo,
                    cred_repo=cred_repo,
                    crypto=crypto,
                    gateway=gateway,
                    storage=storage,
                    zip_processor=zip_processor,
                    db=db,
                    descarga_id=descarga_emitidos.id,
                )

    def test_retenciones_solicitud_verificacion_descarga(self) -> None:
        self._ensure_ready()

        with self._session_local() as db:
            cred_repo = SqlSatCredentialsRepository(db)
            cred = cred_repo.list_all()[0]
            rfc_value = cred.rfc

            repo = SqlSatDescargasRepository(db)
            crypto = FernetSatCrypto()
            gateway = build_sat_gateway()

            params_emitidos = SolicitudDescargaParams(
                rfc_solicitante=rfc_value,
                rfc_emisor=rfc_value,
                fecha_inicial=datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc),
                fecha_final=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                tipo_solicitud="emitidos",
                tipo_descarga="CFDI",
                complemento="",
                estado_comprobante="Vigente",
                tipo_comprobante="",
                rfc_a_cuenta_terceros="",
            )
            descarga_emitidos = crear_solicitud_descarga(
                repo=repo,
                cred_repo=cred_repo,
                crypto=crypto,
                gateway=gateway,
                rfc=rfc_value,
                kind="retenciones",
                params=params_emitidos,
                tag_name="SolicitaDescargaEmitidos",
            )
            print(f"\nRET IdSolicitud emitidos: {descarga_emitidos.id_solicitud}")

        estado_emitidos = self._poll_until_ready(descarga_emitidos.id)
        self.assertNotEqual(estado_emitidos, STATUS_ERROR)

        if estado_emitidos == STATUS_LISTA:
            with self._session_local() as db:
                repo = SqlSatDescargasRepository(db)
                cred_repo = SqlSatCredentialsRepository(db)
                crypto = FernetSatCrypto()
                gateway = build_sat_gateway()
                storage = SatStorageFs()
                zip_processor = LocalSatZipProcessor()
                descargar_y_procesar(
                    repo=repo,
                    cred_repo=cred_repo,
                    crypto=crypto,
                    gateway=gateway,
                    storage=storage,
                    zip_processor=zip_processor,
                    db=db,
                    descarga_id=descarga_emitidos.id,
                )


if __name__ == "__main__":
    unittest.main()
