from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.application.reportes import service


def test_normalize_tipo_declaracion_defaults_to_mensual():
    assert service.normalize_tipo_declaracion(None) == "MENSUAL"


def test_normalize_tipo_declaracion_rejects_invalid_value():
    with pytest.raises(HTTPException) as exc:
        service.normalize_tipo_declaracion("invalid")
    assert exc.value.status_code == 400


def test_resolve_period_or_404_uses_default_month_for_mensual(monkeypatch):
    monkeypatch.setattr(service, "pick_default_period", lambda _db: (2025, 8))
    year, month = service.resolve_period_or_404(
        db=object(),
        tipo_decl=service.TIPO_DECL_MENSUAL,
        year=2025,
        month=None,
    )
    assert (year, month) == (2025, 8)


def test_resolve_period_or_404_raises_when_no_data(monkeypatch):
    monkeypatch.setattr(service, "pick_default_period", lambda _db: (None, None))
    with pytest.raises(HTTPException) as exc:
        service.resolve_period_or_404(
            db=object(),
            tipo_decl=service.TIPO_DECL_MENSUAL,
            year=None,
            month=None,
        )
    assert exc.value.status_code == 404


def test_resolve_mi_rfc_fallback_order():
    data = {"ret_rows": [SimpleNamespace(receptor_rfc="CCC010101CCC")]}
    assert service.resolve_mi_rfc(" AAA010101AAA ", None, data) == "AAA010101AAA"

    declaracion_pdf = SimpleNamespace(rfc="BBB010101BBB")
    assert service.resolve_mi_rfc("", declaracion_pdf, {"ret_rows": []}) == "BBB010101BBB"

    assert service.resolve_mi_rfc("", None, data) == "CCC010101CCC"


def test_build_sat_report_csv_includes_header_and_period():
    data = {
        "plat_ing_siva": 100.0,
        "ingresos_base": 200.0,
        "plat_isr_ret": 5.0,
        "plat_iva_tras": 16.0,
        "plat_iva_ret": 2.0,
        "ingresos_trasl": 32.0,
        "gastos_trasl": 8.0,
    }
    csv_text = service.build_sat_report_csv(data, 2025, 7, "cfdi")
    assert "periodo,ingresos_plataforma_sin_iva" in csv_text
    assert "2025-07" in csv_text
    assert "cfdi" in csv_text


def test_build_acuse_payload_and_checks_returns_empty_when_no_pdf():
    payload, checks = service.build_acuse_payload_and_checks(
        declaracion_pdf=None,
        year=2025,
        month=7,
        mi_rfc="AAA010101AAA",
        data={},
        ingresos_total_sin_iva=0.0,
        iva_trasladado_total=0.0,
    )
    assert payload is None
    assert checks == []


def test_build_acuse_payload_and_checks_builds_expected_checks(monkeypatch):
    fake_payload = {
        "periodo": "2025-07",
        "rfc": "AAA010101AAA",
        "ingresos_totales_mes": 100.0,
        "retenciones_plataformas": 1.0,
        "iva_a_cargo_16": 16.0,
        "iva_acreditable": 8.0,
        "iva_retenido": 2.0,
    }
    monkeypatch.setattr(service, "declaracion_model_to_entity", lambda model: model)
    monkeypatch.setattr(
        service,
        "LocalPdfParser",
        lambda: SimpleNamespace(parse_sat_summary=lambda _text: fake_payload),
    )
    monkeypatch.setattr(
        service,
        "build_declaracion_payload",
        lambda _dec, _parser: fake_payload,
    )

    declaracion_pdf = SimpleNamespace(text_excerpt="dummy")
    data = {
        "plat_isr_ret": 1.0,
        "gastos_trasl": 8.0,
        "plat_iva_ret": 2.0,
    }
    payload, checks = service.build_acuse_payload_and_checks(
        declaracion_pdf=declaracion_pdf,
        year=2025,
        month=7,
        mi_rfc="AAA010101AAA",
        data=data,
        ingresos_total_sin_iva=100.0,
        iva_trasladado_total=16.0,
    )
    assert payload == fake_payload
    assert len(checks) == 7
    assert checks[0]["label"] == "Periodo"
