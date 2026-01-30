import logging
import os

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

DEFAULT_SAT_PASSWORD_SECRET = os.getenv("SAT_PASSWORD_SECRET") or "CjtwIZ6dGe5cwHgrLpW-YowE56KQYd9Uc9onVAO3WCw="
DEFAULT_AUTH_SECRET = os.getenv("CFDI_AUTH_SECRET") or "LaNT9KXAyIgtfHg61SdXK28os1ey1z0nKVkeqvxBXWXD0dOCdgraVq9tgEGOIUS3"
DEFAULT_AUTH_TTL_MINUTES = os.getenv("CFDI_AUTH_TTL_MINUTES") or 2880  # 2 days
DEFAULT_AUTH_PASSWORD_ITERATIONS = os.getenv("CFDI_AUTH_PASSWORD_ITERATIONS") or 390000 # Sube a 300k–600k en prod).
DEFAULT_TIMEOUT_SAT_SECONDS = os.getenv("CFDI_TIMEOUT_SAT_SECONDS") or 200
DEFAULT_SAT_DOWNLOAD_DIR = os.getenv("SAT_DOWNLOAD_DIR") or r"C:\cfdi\xml"

SAT_ENV = os.getenv("SAT_ENV", "uat").lower()
if SAT_ENV not in {"uat", "prod"}:
    raise ValueError(f"Invalid SAT_ENV '{SAT_ENV}'. Use 'uat' or 'prod'.")

SAT_ENDPOINTS = {
    "uat": {
        "cfdi_auth": "https://cu1-cfd-uat-webc-dmtsoli.cloudapp.net/Autenticacion.svc",
        "cfdi_solicitud": "https://cu1-cfd-uat-cse-dmasiva.centralus.cloudapp.azure.com/SolicitaDescargaService.svc",
        "cfdi_verificacion": "https://srvsolicituddescargamaster.cloudapp.net/VerificaSolicitudDescargaService.svc",
        "cfdi_descarga": "https://srvdescargamasivaterceros.cloudapp.net/DescargaMasivaTercerosService.svc",
        "ret_auth": "https://cu1-cfd-uat-webc-dmtsoli.cloudapp.net/Autenticacion.svc",
        "ret_solicitud": "https://cu1-cfd-uat-cse-dmasiva.centralus.cloudapp.azure.com/SolicitaDescargaService.svc",
        "ret_verificacion": "https://srvsolicituddescargamaster.cloudapp.net/VerificaSolicitudDescargaService.svc",
        "ret_descarga": "https://srvdescargamasivaterceros.cloudapp.net/DescargaMasivaTercerosService.svc",
    },
    "prod": {
        "cfdi_auth": "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc",
        "cfdi_solicitud": "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc",
        "cfdi_verificacion": "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc",
        "cfdi_descarga": "https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc",
        "ret_auth": "https://retendescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc",
        "ret_solicitud": "https://retendescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc",
        "ret_verificacion": "https://retendescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc",
        "ret_descarga": "https://retendescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc",
    },
}

SAT_DEFAULTS = SAT_ENDPOINTS[SAT_ENV]
logger.info("SAT environment set to '%s'", SAT_ENV)

class Settings(BaseSettings):
    app_name: str = "CFDI API"
    auth_secret: str = DEFAULT_AUTH_SECRET
    auth_token_ttl_minutes: int = DEFAULT_AUTH_TTL_MINUTES
    auth_password_iterations: int = DEFAULT_AUTH_PASSWORD_ITERATIONS
    sat_password_secret: str = DEFAULT_SAT_PASSWORD_SECRET
    sat_cfdi_auth_url: str = (
        SAT_DEFAULTS["cfdi_auth"]
    )
    sat_cfdi_solicitud_url: str = (
        SAT_DEFAULTS["cfdi_solicitud"]
    )
    sat_cfdi_verificacion_url: str = (
        SAT_DEFAULTS["cfdi_verificacion"]
    )
    sat_cfdi_descarga_url: str = (
        SAT_DEFAULTS["cfdi_descarga"]
    )
    sat_ret_auth_url: str = (
        SAT_DEFAULTS["ret_auth"]
    )
    sat_ret_solicitud_url: str = (
        SAT_DEFAULTS["ret_solicitud"]
    )
    sat_ret_verificacion_url: str = (
        SAT_DEFAULTS["ret_verificacion"]
    )
    sat_ret_descarga_url: str = (
        SAT_DEFAULTS["ret_descarga"]
    )
    sat_timeout_seconds: int = DEFAULT_TIMEOUT_SAT_SECONDS
    sat_download_dir: str = DEFAULT_SAT_DOWNLOAD_DIR
    sat_soap_action_descarga: str = (
        "http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"
    )


settings = Settings()
