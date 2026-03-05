from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adapters.inbound.http.api.v1.schemas.deducciones import (
    DeduccionesCatalogRegimenResponse,
    DeduccionesCatalogResponse,
    DeduccionesCatalogUsoResponse,
)
from app.adapters.inbound.http.deps import get_db, get_required_rfc, require_user
from app.application.reportes.service import load_config_for_rfc, normalize_tipo_declaracion

router = APIRouter(prefix="/deducciones", tags=["deducciones"], dependencies=[Depends(require_user)])


@router.get(
    "/catalogo",
    response_model=DeduccionesCatalogResponse,
    summary="Catalogo de deducciones por RFC",
    description="Devuelve los usos CFDI deducibles para el RFC en header X-RFC.",
)
def deducciones_catalogo(
    tipo_declaracion: str = Query(..., min_length=3),
    x_rfc: str = Depends(get_required_rfc),
    db: Session = Depends(get_db),
) -> DeduccionesCatalogResponse:
    tipo_decl = normalize_tipo_declaracion(tipo_declaracion)
    config, _, regimen = load_config_for_rfc(
        db,
        rfc=x_rfc,
        tipo_declaracion_clave=tipo_decl,
    )
    usos = [
        DeduccionesCatalogUsoResponse(
            clave=str(item.get("clave") or "").strip().upper(),
            descripcion=str(item.get("descripcion") or "").strip(),
            orden=int(item.get("orden") or 0),
        )
        for item in (config.get("usos_cfdi") or [])
        if str(item.get("clave") or "").strip()
    ]
    return DeduccionesCatalogResponse(
        rfc=x_rfc,
        regimen_fiscal=DeduccionesCatalogRegimenResponse(
            clave=regimen.clave,
            descripcion=regimen.descripcion,
            tipo_persona_clave=regimen.tipo_persona_clave,
        ),
        tipo_declaracion=tipo_decl,
        usos_cfdi=usos,
    )
