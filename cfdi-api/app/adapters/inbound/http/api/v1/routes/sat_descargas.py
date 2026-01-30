from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db, get_required_rfc, require_user
from app.adapters.inbound.http.api.v1.schemas.sat_descargas import (
    SatDescargaCreateRequest,
    SatDescargaResponse,
)
from app.adapters.outbound.db.repositories.sat_credentials import SqlSatCredentialsRepository
from app.adapters.outbound.db.repositories.sat_descargas import SqlSatDescargasRepository
from app.adapters.outbound.files.sat_storage_fs import SatStorageFs
from app.adapters.services.sat.crypto.crypto_service import FernetSatCrypto
from app.adapters.services.sat.sat_gateway import SoapSatGateway
from app.application.sat.descargas_service import crear_solicitud_descarga
from app.application.sat.dto import SolicitudDescargaParams
from app.infra.queue.rq_tasks import verificar_descarga_job

router = APIRouter(prefix="/sat/descargas", tags=["sat-descargas"], dependencies=[Depends(require_user)])


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
        paquetes=model.paquetes,
        link_descarga=model.link_descarga,
        zip_path=model.zip_path,
        attempts=model.attempts,
        next_check_at=model.next_check_at,
        last_error=model.last_error,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.post("", response_model=SatDescargaResponse)
def crear_descarga(
    payload: SatDescargaCreateRequest,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> SatDescargaResponse:
    rfc_value = (x_rfc or "").strip().upper()

    repo = SqlSatDescargasRepository(db)
    cred_repo = SqlSatCredentialsRepository(db)
    crypto = FernetSatCrypto()
    gateway = SoapSatGateway()

    params = SolicitudDescargaParams(
        rfc_solicitante=rfc_value,
        fecha_inicial=payload.fecha_inicial,
        fecha_final=payload.fecha_final,
        tipo_solicitud=payload.tipo_solicitud,
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

    try:
        descarga = crear_solicitud_descarga(
            repo=repo,
            cred_repo=cred_repo,
            crypto=crypto,
            gateway=gateway,
            rfc=rfc_value,
            kind=payload.kind,
            params=params,
        )
        verificar_descarga_job(descarga.id, schedule_next=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(descarga)


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


@router.get("/{descarga_id}/zip")
def download_zip(
    descarga_id: int,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> Response:
    repo = SqlSatDescargasRepository(db)
    descarga = repo.get_by_id(descarga_id)
    if not descarga:
        raise HTTPException(status_code=404, detail="Descarga no encontrada.")
    if descarga.rfc != (x_rfc or "").strip().upper():
        raise HTTPException(status_code=403, detail="RFC no autorizado.")
    if not descarga.paquetes:
        raise HTTPException(status_code=409, detail="Descarga sin paquetes.")
    if len(descarga.paquetes) != 1:
        raise HTTPException(status_code=409, detail="Descarga con multiples paquetes.")

    storage = SatStorageFs()
    zip_bytes = storage.open_zip(descarga.rfc, descarga.paquetes[0])
    filename = f"{descarga.rfc}_{descarga.paquetes[0]}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
