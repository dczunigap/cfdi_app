from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.application.sat.dto import SolicitudDescargaParams, VerificacionResult
from app.domain.sat.entities import SatDescarga
from app.ports.sat_credentials_repo import SatCredentialsRepository
from app.ports.sat_crypto import SatCrypto
from app.ports.sat_descargas_repo import SatDescargasRepository
from app.ports.sat_gateway import SatGateway
from app.ports.sat_storage import SatStorage
from app.ports.sat_zip_processor import SatZipProcessor

STATUS_SOLICITADA = "SOLICITADA"
STATUS_EN_PROCESO = "EN_PROCESO"
STATUS_LISTA = "LISTA"
STATUS_DESCARGANDO = "DESCARGANDO"
STATUS_COMPLETADA = "COMPLETADA"
STATUS_SIN_RESULTADOS = "SIN_RESULTADOS"
STATUS_EXPIRADA = "EXPIRADA"
STATUS_ERROR = "ERROR"


def crear_solicitud_descarga(
    repo: SatDescargasRepository,
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    rfc: str,
    kind: str,
    params: SolicitudDescargaParams,
    soap_action: str | None = None,
    tag_name: str = "SolicitaDescargaEmitidos",
) -> SatDescarga:
    key_material, token = _authenticate(cred_repo, crypto, gateway, rfc, kind)
    solicitud = gateway.solicitar_descarga(
        kind=kind,
        key_material=key_material,
        params=params,
        access_token=token,
        soap_action=soap_action,
        tag_name=tag_name,
    )
    if not solicitud.id_solicitud:
        raise ValueError(solicitud.mensaje or "Respuesta sin IdSolicitud.")
    now = datetime.now(timezone.utc)
    return repo.create(
        rfc=rfc,
        kind=kind,
        tipo_solicitud=params.tipo_solicitud,
        anio_filtro=params.fecha_inicial.year if params.fecha_inicial else None,
        mes_filtro=params.fecha_inicial.month if params.fecha_inicial else None,
        id_solicitud=solicitud.id_solicitud,
        estado=STATUS_SOLICITADA,
        codigo_estado=solicitud.codigo_estado,
        mensaje_estado=solicitud.mensaje,
        paquetes=[],
        link_descarga=None,
        zip_path=None,
        attempts=0,
        next_check_at=now,
    )


def verificar_descarga(
    repo: SatDescargasRepository,
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    descarga_id: int,
    soap_action: str | None = None,
) -> SatDescarga | None:
    descarga = repo.get_by_id(descarga_id)
    if not descarga or not descarga.id_solicitud:
        return None

    key_material, token = _authenticate(cred_repo, crypto, gateway, descarga.rfc, descarga.kind)
    result = gateway.verificar_descarga(
        kind=descarga.kind,
        key_material=key_material,
        rfc_solicitante=descarga.rfc,
        id_solicitud=descarga.id_solicitud,
        access_token=token,
        soap_action=soap_action,
    )

    estado = _map_estado(result)
    attempts = descarga.attempts + 1 if estado in {STATUS_EN_PROCESO} else descarga.attempts
    next_check_at = _next_check_at(attempts) if estado == STATUS_EN_PROCESO else None
    link_descarga = descarga.link_descarga
    if estado == STATUS_LISTA:
        link_descarga = link_descarga or f"/api/v1/sat/descargas/{descarga.id}/zip"

    return repo.update(
        descarga.id,
        estado=estado,
        paquetes=result.paquetes or [],
        attempts=attempts,
        next_check_at=next_check_at,
        link_descarga=link_descarga,
        codigo_estado=result.codigo_estado,
        mensaje_estado=result.mensaje,
    )


def descargar_y_procesar(
    repo: SatDescargasRepository,
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    storage: SatStorage,
    zip_processor: SatZipProcessor,
    db: Any,
    descarga_id: int,
    soap_action: str | None = None,
) -> SatDescarga | None:
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        return None
    if not descarga.paquetes:
        return repo.update(descarga.id, estado=STATUS_SIN_RESULTADOS, next_check_at=None)

    repo.update(descarga.id, estado=STATUS_DESCARGANDO)

    key_material, token = _authenticate(cred_repo, crypto, gateway, descarga.rfc, descarga.kind)
    last_zip_path: str | None = None

    for id_paquete in descarga.paquetes:
        descarga_result = gateway.descargar_paquete(
            kind=descarga.kind,
            key_material=key_material,
            rfc_solicitante=descarga.rfc,
            id_paquete=id_paquete,
            access_token=token,
            soap_action=soap_action,
        )
        if not descarga_result.zip_bytes:
            return repo.update(
                descarga.id,
                estado=STATUS_ERROR,
                codigo_estado=descarga_result.codigo_estado,
                mensaje_estado=descarga_result.mensaje,
            )
        last_zip_path = storage.save_zip(descarga.rfc, id_paquete, descarga_result.zip_bytes)
        zip_processor.process_zip(db, descarga_result.zip_bytes)

    return repo.update(
        descarga.id,
        estado=STATUS_COMPLETADA,
        zip_path=last_zip_path if len(descarga.paquetes) == 1 else descarga.zip_path,
    )


def _authenticate(
    cred_repo: SatCredentialsRepository,
    crypto: SatCrypto,
    gateway: SatGateway,
    rfc: str,
    kind: str,
) -> tuple[object, str]:
    cred = cred_repo.get_by_rfc(rfc)
    if not cred:
        raise ValueError("RFC sin credenciales.")
    password = crypto.decrypt_text(cred.pfx_password_encrypted)
    pfx_bytes = crypto.decrypt_bytes(cred.pfx_encrypted)
    key_material = gateway.load_key_material(pfx_bytes, password)
    token = gateway.autenticar(kind=kind, key_material=key_material)
    return key_material, token


def _map_estado(result: VerificacionResult) -> str:
    estado_raw = (result.estado_solicitud or "").strip().upper()
    if result.paquetes:
        return STATUS_LISTA
    if estado_raw in {"1", "EN PROCESO", "EN_PROCESO"}:
        return STATUS_EN_PROCESO
    if estado_raw in {"2", "TERMINADA", "TERMINADO"}:
        return STATUS_SIN_RESULTADOS
    if estado_raw in {"3", "RECHAZADA", "RECHAZADO", "ERROR"}:
        return STATUS_ERROR
    if estado_raw in {"4", "VENCIDA", "EXPIRADA", "EXPIRADO"}:
        return STATUS_EXPIRADA
    return STATUS_EN_PROCESO


def _next_check_at(attempts: int) -> datetime:
    now = datetime.now(timezone.utc)
    if attempts <= 5:
        return now + timedelta(minutes=1)
    if attempts <= 12:
        return now + timedelta(minutes=5)
    if attempts <= 20:
        return now + timedelta(minutes=15)
    return now + timedelta(minutes=60)
