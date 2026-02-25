from __future__ import annotations

import pytest

from app.adapters.services.sat.soap.actions import (
    SOAP_CFDI_ACTION_DESCARGA,
    SOAP_CFDI_ACTION_AUTENTICA,
    SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
    SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
    SOAP_CFDI_ACTION_VERIFICA,
    SOAP_RETENCIONES_ACTION_AUTENTICA,
    SOAP_RETENCIONES_ACTION_DESCARGA,
    SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS,
    SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS,
    SOAP_RETENCIONES_ACTION_VERIFICA,
    SatSoapActions,
)
from app.adapters.services.sat.soap.kind import is_retenciones_kind, normalize_sat_kind
from app.adapters.services.sat.soap import descarga_workflow as workflow


def test_normalize_sat_kind_trims_and_lowercases() -> None:
    assert normalize_sat_kind("  CfDi  ") == "cfdi"


@pytest.mark.parametrize("value", ["retenciones", "Retencion", " RET "])
def test_is_retenciones_kind_accepts_variants(value: str) -> None:
    assert is_retenciones_kind(value) is True


def test_actions_for_kind_cfdi_default() -> None:
    actions = SatSoapActions.for_kind("")
    assert actions.autentica == SOAP_CFDI_ACTION_AUTENTICA
    assert actions.solicita_emitidos == SOAP_CFDI_ACTION_SOLICITA_EMITIDOS
    assert actions.solicita_recibidos == SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS
    assert actions.verifica == SOAP_CFDI_ACTION_VERIFICA
    assert actions.descarga == SOAP_CFDI_ACTION_DESCARGA


def test_actions_for_kind_retenciones() -> None:
    actions = SatSoapActions.for_kind("ret")
    assert actions.autentica == SOAP_RETENCIONES_ACTION_AUTENTICA
    assert actions.solicita_emitidos == SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS
    assert actions.solicita_recibidos == SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS
    assert actions.verifica == SOAP_RETENCIONES_ACTION_VERIFICA
    assert actions.descarga == SOAP_RETENCIONES_ACTION_DESCARGA


def test_actions_for_kind_unknown_raises() -> None:
    with pytest.raises(ValueError):
        SatSoapActions.for_kind("otro")


def test_should_log_xml_error_fault() -> None:
    xml_text = "<Envelope><Body><Fault></Fault></Body></Envelope>"
    assert workflow._should_log_xml_error(xml_text) is True


def test_should_log_xml_error_when_result_tag_missing() -> None:
    xml_text = "<Envelope><Body></Body></Envelope>"
    assert workflow._should_log_xml_error(xml_text, result_tag="X") is True


def test_should_log_xml_error_when_code_is_error() -> None:
    xml_text = (
        "<Envelope><Body>"
        "<SolicitaDescargaEmitidosResult CodEstatus=\"300\" IdSolicitud=\"1\" />"
        "</Body></Envelope>"
    )
    assert (
        workflow._should_log_xml_error(
            xml_text,
            result_tag="SolicitaDescargaEmitidosResult",
            code_attr="CodEstatus",
            require_id_attr="IdSolicitud",
        )
        is True
    )


def test_should_log_xml_error_when_code_is_success() -> None:
    xml_text = (
        "<Envelope><Body>"
        "<SolicitaDescargaEmitidosResult CodEstatus=\"5000\" IdSolicitud=\"1\" />"
        "</Body></Envelope>"
    )
    assert (
        workflow._should_log_xml_error(
            xml_text,
            result_tag="SolicitaDescargaEmitidosResult",
            code_attr="CodEstatus",
            require_id_attr="IdSolicitud",
        )
        is False
    )


def test_should_log_xml_error_when_id_missing() -> None:
    xml_text = (
        "<Envelope><Body>"
        "<SolicitaDescargaEmitidosResult CodEstatus=\"5000\" />"
        "</Body></Envelope>"
    )
    assert (
        workflow._should_log_xml_error(
            xml_text,
            result_tag="SolicitaDescargaEmitidosResult",
            code_attr="CodEstatus",
            require_id_attr="IdSolicitud",
        )
        is True
    )


def test_should_log_xml_error_text_tag_present() -> None:
    xml_text = "<Envelope><Body><RespuestaDescargaMasivaTercerosSalida>xxx</RespuestaDescargaMasivaTercerosSalida></Body></Envelope>"
    assert workflow._should_log_xml_error(xml_text, text_tag="RespuestaDescargaMasivaTercerosSalida") is False


def test_should_log_xml_error_text_tag_missing() -> None:
    xml_text = "<Envelope><Body></Body></Envelope>"
    assert workflow._should_log_xml_error(xml_text, text_tag="RespuestaDescargaMasivaTercerosSalida") is True
