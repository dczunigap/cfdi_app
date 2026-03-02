from __future__ import annotations

import pytest

from app.adapters.inbound.http.api.v1.routes.sat_descargas import (
    _resolve_sat_request_shape,
)
from app.adapters.inbound.http.api.v1.schemas.sat_descargas import (
    SatDescargaCreateRequest,
)
from app.adapters.services.sat.soap.descarga_requests import _normalize_tipo_solicitud


def _base_payload() -> dict:
    return {
        "kind": "cfdi",
        "fecha_inicial": "2026-01-01T00:00:00",
        "fecha_final": "2026-01-31T23:59:59",
    }


def test_legacy_tipo_solicitud_emitidos_maps_to_direction_and_cfdi() -> None:
    payload = SatDescargaCreateRequest(**(_base_payload() | {"tipo_solicitud": "emitidos"}))
    direccion, tipo = _resolve_sat_request_shape(payload)
    assert direccion == "emitidos"
    assert tipo == "CFDI"


def test_new_shape_resolves_direction_and_download_type() -> None:
    payload = SatDescargaCreateRequest(
        **(
            _base_payload()
            | {"direccion_solicitud": "recibidos", "tipo_descarga": "metadata"}
        )
    )
    direccion, tipo = _resolve_sat_request_shape(payload)
    assert direccion == "recibidos"
    assert tipo == "Metadata"


def test_invalid_legacy_tipo_solicitud_raises() -> None:
    payload = SatDescargaCreateRequest(**(_base_payload() | {"tipo_solicitud": "emitidosx"}))
    with pytest.raises(ValueError):
        _resolve_sat_request_shape(payload)


def test_soap_tipo_solicitud_normalization_accepts_only_sat_values() -> None:
    assert _normalize_tipo_solicitud("CFDI") == "CFDI"
    assert _normalize_tipo_solicitud("metadata") == "Metadata"
    with pytest.raises(ValueError):
        _normalize_tipo_solicitud("emitidos")
