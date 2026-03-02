from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db, get_required_rfc, require_user
from app.adapters.inbound.http.api.v1.schemas.sat_descargas import (
    SatDescargaCreateRequest,
    SatDescargaResponse,
)
from app.adapters.outbound.db.repositories.sat_credentials import SqlSatCredentialsRepository
from app.adapters.outbound.db.repositories.sat_descargas import SqlSatDescargasRepository
from app.adapters.outbound.db.repositories.user_rfcs import SqlUserRfcsRepository
from app.adapters.outbound.files.storage_factory import build_storage
from app.adapters.services.parsers.sat_zip_processor import LocalSatZipProcessor
from app.adapters.services.sat.crypto.crypto_service import FernetSatCrypto
from app.adapters.services.sat.gateway_factory import build_sat_gateway
from app.application.sat.descargas_service import (
    STATUS_LISTA,
    crear_solicitud_descarga,
    descargar_y_procesar,
    verificar_descarga,
)
from app.application.sat.dto import SolicitudDescargaParams
from app.core.config import settings

router = APIRouter(prefix="/sat/descargas", tags=["sat-descargas"], dependencies=[Depends(require_user)])


def _normalize_direccion_solicitud(value: str | None) -> str:
    normalized = (value or "emitidos").strip().lower()
    if normalized not in {"emitidos", "recibidos"}:
        raise ValueError("direccion_solicitud invalida; usa 'emitidos' o 'recibidos'.")
    return normalized


def _normalize_tipo_descarga(value: str | None) -> str:
    normalized = (value or "CFDI").strip().lower()
    if normalized == "cfdi":
        return "CFDI"
    if normalized == "metadata":
        return "Metadata"
    raise ValueError("tipo_descarga invalido; usa 'CFDI' o 'Metadata'.")


def _resolve_sat_request_shape(payload: SatDescargaCreateRequest) -> tuple[str, str]:
    direccion_solicitud = payload.direccion_solicitud
    tipo_descarga = payload.tipo_descarga
    legacy = (payload.tipo_solicitud or "").strip().lower()

    if legacy:
        if legacy in {"emitidos", "recibidos"}:
            if not direccion_solicitud:
                direccion_solicitud = legacy
        elif legacy in {"cfdi", "metadata"}:
            if not tipo_descarga:
                tipo_descarga = legacy
        else:
            raise ValueError(
                "tipo_solicitud legacy invalido; usa direccion_solicitud/tipo_descarga."
            )

    return _normalize_direccion_solicitud(direccion_solicitud), _normalize_tipo_descarga(
        tipo_descarga
    )


def _to_response(model) -> SatDescargaResponse:
    return SatDescargaResponse(
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
        paquetes=model.paquetes,
        link_descarga=model.link_descarga,
        zip_path=model.zip_path,
        attempts=model.attempts,
        next_check_at=model.next_check_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.post("", response_model=SatDescargaResponse)
def crear_descarga(
    payload: SatDescargaCreateRequest,
    x_rfc: str = Depends(get_required_rfc),
    user=Depends(require_user),
    db: Session = Depends(get_db),
) -> SatDescargaResponse:
    rfc_value = (x_rfc or "").strip().upper()

    repo = SqlSatDescargasRepository(db)
    cred_repo = SqlSatCredentialsRepository(db)
    rfc_repo = SqlUserRfcsRepository(db)
    crypto = FernetSatCrypto()
    gateway = build_sat_gateway()

    if not rfc_repo.is_allowed(user.id, rfc_value):
        raise HTTPException(status_code=403, detail="RFC no autorizado para el usuario.")

    try:
        direccion_solicitud, tipo_descarga = _resolve_sat_request_shape(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    params = SolicitudDescargaParams(
        rfc_solicitante=rfc_value,
        fecha_inicial=payload.fecha_inicial,
        fecha_final=payload.fecha_final,
        kind=payload.kind,
        tipo_solicitud=direccion_solicitud,
        tipo_descarga=tipo_descarga,
        rfc_emisor=payload.rfc_emisor,
        rfc_receptor=payload.rfc_receptor,
        rfc_a_cuenta_terceros=payload.rfc_a_cuenta_terceros,
        tipo_comprobante=payload.tipo_comprobante,
        complemento=payload.complemento,
        estado_comprobante=payload.estado_comprobante,
        folio=payload.folio,
        uuid=payload.uuid,
        rfc_receptores=payload.rfc_receptores or [],
    )

    tag_name = (
        "SolicitaDescargaRecibidos"
        if direccion_solicitud == "recibidos"
        else "SolicitaDescargaEmitidos"
    )
    try:
        descarga = crear_solicitud_descarga(
            repo=repo,
            cred_repo=cred_repo,
            crypto=crypto,
            gateway=gateway,
            rfc=rfc_value,
            kind=payload.kind,
            params=params,
            tag_name=tag_name,
        )
        if settings.sat_autoverify:
            try:
                from app.infra.queue.rq_tasks import verificar_descarga_job
                verificar_descarga_job(descarga.id, schedule_next=False)
            except ModuleNotFoundError:
                pass
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(descarga)


@router.get("", response_model=list[SatDescargaResponse])
def list_descargas(
    estado: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    x_rfc: str = Depends(get_required_rfc),
    user=Depends(require_user),
    db: Session = Depends(get_db),
) -> list[SatDescargaResponse]:
    rfc_value = (x_rfc or "").strip().upper()
    rfc_repo = SqlUserRfcsRepository(db)
    if not rfc_repo.is_allowed(user.id, rfc_value):
        raise HTTPException(status_code=403, detail="RFC no autorizado para el usuario.")

    repo = SqlSatDescargasRepository(db)
    rows = repo.list_by_rfc(rfc_value, estado, limit, offset)
    return [_to_response(row) for row in rows]


@router.get("/{descarga_id}", response_model=SatDescargaResponse)
def get_descarga(
    descarga_id: int,
    db: Session = Depends(get_db),
) -> SatDescargaResponse:
    repo = SqlSatDescargasRepository(db)
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    return _to_response(descarga)


@router.post("/{descarga_id}/verify", response_model=SatDescargaResponse)
def verify_descarga(
    descarga_id: int,
    x_rfc: str = Depends(get_required_rfc),
    user=Depends(require_user),
    db: Session = Depends(get_db),
) -> SatDescargaResponse:
    repo = SqlSatDescargasRepository(db)
    rfc_repo = SqlUserRfcsRepository(db)
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    if descarga.rfc != (x_rfc or "").strip().upper():
        raise HTTPException(status_code=403, detail="RFC no autorizado.")
    if not rfc_repo.is_allowed(user.id, descarga.rfc):
        raise HTTPException(status_code=403, detail="RFC no autorizado para el usuario.")

    cred_repo = SqlSatCredentialsRepository(db)
    crypto = FernetSatCrypto()
    gateway = build_sat_gateway()
    updated = verificar_descarga(
        repo=repo,
        cred_repo=cred_repo,
        crypto=crypto,
        gateway=gateway,
        descarga_id=descarga_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    return _to_response(updated)


@router.get("/{descarga_id}/zip")
def download_zip(
    descarga_id: int,
    x_rfc: str = Depends(get_required_rfc),
    user=Depends(require_user),
    db: Session = Depends(get_db),
) -> Response:
    repo = SqlSatDescargasRepository(db)
    rfc_repo = SqlUserRfcsRepository(db)
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    if descarga.rfc != (x_rfc or "").strip().upper():
        raise HTTPException(status_code=403, detail="RFC no autorizado.")
    if not rfc_repo.is_allowed(user.id, descarga.rfc):
        raise HTTPException(status_code=403, detail="RFC no autorizado para el usuario.")
    if not descarga.paquetes:
        raise HTTPException(status_code=409, detail="Descarga sin paquetes.")
    if len(descarga.paquetes) != 1:
        raise HTTPException(status_code=409, detail="Descarga con multiples paquetes.")

    storage = build_storage()
    zip_bytes = storage.open_zip(descarga.rfc, descarga.paquetes[0])
    filename = f"{descarga.rfc}_{descarga.paquetes[0]}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{descarga_id}/process", response_model=SatDescargaResponse)
def process_descarga(
    descarga_id: int,
    x_rfc: str = Depends(get_required_rfc),
    user=Depends(require_user),
    db: Session = Depends(get_db),
) -> SatDescargaResponse:
    repo = SqlSatDescargasRepository(db)
    rfc_repo = SqlUserRfcsRepository(db)
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    if descarga.rfc != (x_rfc or "").strip().upper():
        raise HTTPException(status_code=403, detail="RFC no autorizado.")
    if not rfc_repo.is_allowed(user.id, descarga.rfc):
        raise HTTPException(status_code=403, detail="RFC no autorizado para el usuario.")

    cred_repo = SqlSatCredentialsRepository(db)
    crypto = FernetSatCrypto()
    gateway = build_sat_gateway()
    storage = build_storage()
    zip_processor = LocalSatZipProcessor()

    updated = verificar_descarga(
        repo=repo,
        cred_repo=cred_repo,
        crypto=crypto,
        gateway=gateway,
        descarga_id=descarga_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")

    if updated.estado == STATUS_LISTA:
        updated = descargar_y_procesar(
            repo=repo,
            cred_repo=cred_repo,
            crypto=crypto,
            gateway=gateway,
            storage=storage,
            zip_processor=zip_processor,
            db=db,
            descarga_id=descarga_id,
        ) or updated

    return _to_response(updated)


@router.delete("/{descarga_id}")
def delete_descarga(
    descarga_id: int,
    x_rfc: str = Depends(get_required_rfc),
    user=Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    repo = SqlSatDescargasRepository(db)
    rfc_repo = SqlUserRfcsRepository(db)
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    if descarga.rfc != (x_rfc or "").strip().upper():
        raise HTTPException(status_code=403, detail="RFC no autorizado.")
    if not rfc_repo.is_allowed(user.id, descarga.rfc):
        raise HTTPException(status_code=403, detail="RFC no autorizado para el usuario.")

    repo.delete(descarga_id)
    return {"ok": True}
