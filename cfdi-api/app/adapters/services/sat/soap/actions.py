from dataclasses import dataclass

from app.adapters.services.sat.soap.kind import is_retenciones_kind, normalize_sat_kind
from app.core.config import settings


@dataclass(frozen=True)
class SatSoapActions:
    autentica: str
    solicita_emitidos: str
    solicita_recibidos: str
    verifica: str
    descarga: str

    @staticmethod
    def for_kind(kind: str) -> "SatSoapActions":
        normalized = normalize_sat_kind(kind)
        if is_retenciones_kind(kind):
            return SatSoapActions(
                autentica=SOAP_RETENCIONES_ACTION_AUTENTICA,
                solicita_emitidos=SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS,
                solicita_recibidos=SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS,
                verifica=SOAP_RETENCIONES_ACTION_VERIFICA,
                descarga=SOAP_RETENCIONES_ACTION_DESCARGA,
            )
        if normalized == "cfdi" or not normalized:
            return SatSoapActions(
                autentica=SOAP_CFDI_ACTION_AUTENTICA,
                solicita_emitidos=SOAP_CFDI_ACTION_SOLICITA_EMITIDOS,
                solicita_recibidos=SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS,
                verifica=SOAP_CFDI_ACTION_VERIFICA,
                descarga=SOAP_CFDI_ACTION_DESCARGA,
            )
        raise ValueError(f"Tipo SAT no soportado: {kind}")

# CFDI SOAP Actions
SOAP_CFDI_ACTION_AUTENTICA = "http://DescargaMasivaTerceros.gob.mx/IAutenticacion/Autentica"
SOAP_CFDI_ACTION_SOLICITA_EMITIDOS = (
    "http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescargaEmitidos"
)
SOAP_CFDI_ACTION_SOLICITA_RECIBIDOS = (
    "http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescargaRecibidos"
)
SOAP_CFDI_ACTION_VERIFICA = (
    "http://DescargaMasivaTerceros.sat.gob.mx/IVerificaSolicitudDescargaService/VerificaSolicitudDescarga"
)
SOAP_CFDI_ACTION_DESCARGA = "http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"

# Retenciones SOAP Actions
SOAP_RETENCIONES_ACTION_AUTENTICA = "http://DescargaMasivaTerceros.gob.mx/IAutenticacion/Autentica"
SOAP_RETENCIONES_ACTION_SOLICITA_EMITIDOS = (
    "http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescargaEmitidos"
)
SOAP_RETENCIONES_ACTION_SOLICITA_RECIBIDOS = (
    "http://DescargaMasivaTerceros.sat.gob.mx/ISolicitaDescargaService/SolicitaDescargaRecibidos"
)
SOAP_RETENCIONES_ACTION_VERIFICA = (
    "http://DescargaMasivaTerceros.sat.gob.mx/IVerificaSolicitudDescargaService/VerificaSolicitudDescarga"
)
SOAP_RETENCIONES_ACTION_DESCARGA = "http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"
