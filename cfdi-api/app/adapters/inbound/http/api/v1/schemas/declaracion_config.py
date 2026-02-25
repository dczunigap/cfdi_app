from __future__ import annotations

from pydantic import BaseModel


class DeclaracionConfigCatalogTipoDeclResponse(BaseModel):
    clave: str
    descripcion: str
    activo: bool


class DeclaracionConfigCatalogRegimenResponse(BaseModel):
    id: int
    tipo_persona_clave: str
    clave: str
    descripcion: str
    activo: bool


class DeclaracionConfigCatalogUsoResponse(BaseModel):
    clave: str
    descripcion: str
    tipo_declaracion_clave: str
    activo: bool


class DeclaracionConfigCatalogsResponse(BaseModel):
    tipos_declaracion: list[DeclaracionConfigCatalogTipoDeclResponse]
    regimenes_fiscales: list[DeclaracionConfigCatalogRegimenResponse]
    usos_cfdi_deduccion: list[DeclaracionConfigCatalogUsoResponse]


class DeclaracionConfigUsoRequest(BaseModel):
    clave: str
    orden: int | None = None


class DeclaracionConfigUpsertRequest(BaseModel):
    regimen_fiscal_clave: str
    tipo_declaracion_clave: str
    activo: bool = True
    incluir_acumulado_mensual_en_anual: bool = True
    usos_cfdi: list[DeclaracionConfigUsoRequest]


class DeclaracionConfigRegimenResponse(BaseModel):
    id: int
    clave: str
    descripcion: str | None = None
    tipo_persona_clave: str


class DeclaracionConfigUsoResponse(BaseModel):
    clave: str
    descripcion: str
    orden: int


class DeclaracionConfigGetResponse(BaseModel):
    regimen_fiscal: DeclaracionConfigRegimenResponse
    tipo_declaracion_clave: str
    activo: bool
    incluir_acumulado_mensual_en_anual: bool
    usos_cfdi: list[DeclaracionConfigUsoResponse]


class DeclaracionConfigUpsertResponse(BaseModel):
    ok: bool = True
    config_id: int
