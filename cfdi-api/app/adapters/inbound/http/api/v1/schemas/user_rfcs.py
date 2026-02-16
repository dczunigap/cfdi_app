from __future__ import annotations

from pydantic import BaseModel


class UserRfcCreateRequest(BaseModel):
    user_id: int
    rfc: str
    regimen_fiscal_clave: str


class UserRfcResponse(BaseModel):
    user_id: int
    rfc: str
    tipo_persona_clave: str
    regimen_fiscal_clave: str
    regimen_fiscal_descripcion: str
