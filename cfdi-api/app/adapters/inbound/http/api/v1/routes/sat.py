from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.adapters.inbound.http.deps import get_db, get_required_rfc
from app.adapters.inbound.http.api.v1.schemas.sat import SatAuthRequest, SatCredentialResponse
from app.adapters.outbound.db.repositories.sat_credentials import SqlSatCredentialsRepository
from app.adapters.services.sat.crypto.crypto_service import FernetSatCrypto
from app.adapters.services.sat.sat_gateway import SoapSatGateway
from app.application.sat.use_cases import (
    authenticate,
    delete_credentials,
    list_credentials as list_sat_credentials,
    upsert_credentials as upsert_sat_credentials,
)

router = APIRouter(prefix="/sat", tags=["sat"])


@router.get("/credentials", response_model=list[SatCredentialResponse])
def list_credentials_route(db: Session = Depends(get_db)) -> list[SatCredentialResponse]:
    repo = SqlSatCredentialsRepository(db)
    rows = list_sat_credentials(repo)
    return [
        SatCredentialResponse(
            rfc=row.rfc,
            created_at=row.created_at,
            updated_at=row.updated_at,
            has_password=bool(row.pfx_password_encrypted),
            has_pfx=bool(row.pfx_encrypted),
        )
        for row in rows
    ]


@router.post("/credentials")
async def upsert_credentials_route(
    rfc: str = Form(...),
    key_password: str = Form(...),
    pfx_file: UploadFile | None = File(None),
    cert_file: UploadFile | None = File(None),
    key_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> dict:
    rfc_value = _normalize_rfc(rfc)
    if not rfc_value:
        raise HTTPException(status_code=400, detail="RFC requerido")

    if not key_password.strip():
        raise HTTPException(status_code=400, detail="Password requerido.")

    if pfx_file and (cert_file or key_file):
        raise HTTPException(status_code=400, detail="Usa PFX o CER/KEY, no ambos.")

    if not pfx_file and (not cert_file or not key_file):
        raise HTTPException(status_code=400, detail="PFX o archivos .cer/.key son requeridos.")

    pfx_bytes = None
    if pfx_file:
        pfx_bytes = await pfx_file.read()
        if not pfx_bytes:
            raise HTTPException(status_code=400, detail="Archivo PFX vacio.")
    cert_bytes = await cert_file.read() if cert_file else None
    key_bytes = await key_file.read() if key_file else None

    repo = SqlSatCredentialsRepository(db)
    crypto = FernetSatCrypto()
    gateway = SoapSatGateway()
    try:
        upsert_sat_credentials(
            repo=repo,
            crypto=crypto,
            gateway=gateway,
            rfc=rfc_value,
            pfx_bytes=pfx_bytes,
            cert_bytes=cert_bytes,
            key_bytes=key_bytes,
            key_password=key_password.strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error guardando credenciales: {exc}") from exc
    return {"status": "ok", "rfc": rfc_value}


@router.delete("/credentials/{rfc}")
def delete_credentials(rfc: str, db: Session = Depends(get_db)) -> dict:
    rfc_value = _normalize_rfc(rfc)
    if not rfc_value:
        raise HTTPException(status_code=400, detail="RFC requerido")
    repo = SqlSatCredentialsRepository(db)
    existing = repo.get_by_rfc(rfc_value)
    if not existing:
        raise HTTPException(status_code=404, detail="RFC sin credenciales.")
    delete_credentials(repo, rfc_value)
    return {"status": "deleted", "rfc": rfc_value}


@router.post("/auth")
def sat_auth(
    payload: SatAuthRequest,
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> dict:
    rfc_value = _normalize_rfc(x_rfc)

    repo = SqlSatCredentialsRepository(db)
    crypto = FernetSatCrypto()
    gateway = SoapSatGateway()
    try:
        token = authenticate(
            repo=repo,
            crypto=crypto,
            gateway=gateway,
            rfc=rfc_value,
            kind=payload.kind,
            soap_action=payload.soap_action,
            to_url=payload.to_url,
            action=payload.action,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Credenciales invalidas: {exc}") from exc
    return {"token": token}


def _normalize_rfc(value: str | None) -> str:
    return (value or "").strip().upper()
