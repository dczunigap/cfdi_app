# Configuración básica
# Cambia MI_RFC por tu RFC real cuando lo uses en tu PC.
# Configura el RFC aqui (se usa para buscar credenciales en la BD).
MI_RFC = "ZUPD8402022A2"

# Clave Fernet para cifrar el password en BD (32 bytes base64 urlsafe).
SAT_PASSWORD_SECRET = "zB3Q9O0mA0N3fR55e2k6Qn9sH6e1t2h3V9nQ1vX2yZ0="

# Endpoints SAT Descarga Masiva (2026)
SAT_CFDI_AUTH_URL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc"
SAT_CFDI_SOLICITUD_URL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc"
SAT_CFDI_VERIFICACION_URL = "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc"
SAT_CFDI_DESCARGA_URL = "https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc"

# Endpoints SAT Retenciones Descarga Masiva (2026)
SAT_RET_AUTH_URL = "https://retendescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc"
SAT_RET_SOLICITUD_URL = "https://retendescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc"
SAT_RET_VERIFICACION_URL = "https://retendescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc"
SAT_RET_DESCARGA_URL = "https://retendescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc"

SAT_TIMEOUT_SECONDS = 200

# SOAPAction (permite ajustar segun el WSDL)
SAT_SOAP_ACTION_DESCARGA = "http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"
