from __future__ import annotations

from pydantic import BaseModel


class DeduccionesCatalogRegimenResponse(BaseModel):
    clave: str
    descripcion: str | None = None
    tipo_persona_clave: str


class DeduccionesCatalogUsoResponse(BaseModel):
    clave: str
    descripcion: str
    orden: int


class DeduccionesCatalogResponse(BaseModel):
    rfc: str
    regimen_fiscal: DeduccionesCatalogRegimenResponse
    tipo_declaracion: str
    usos_cfdi: list[DeduccionesCatalogUsoResponse]
