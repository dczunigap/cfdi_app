from app.core.config import settings

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
SOAP_ACTION_DESCARGA = settings.sat_soap_action_descarga

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
SOAP_RETENCIONES_ACTION_DESCARGA = settings.sat_soap_action_descarga
