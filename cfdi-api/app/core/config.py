import os

from pydantic_settings import BaseSettings


DEFAULT_SAT_PASSWORD_SECRET = os.getenv("SAT_PASSWORD_SECRET") or "CjtwIZ6dGe5cwHgrLpW-YowE56KQYd9Uc9onVAO3WCw="
DEFAULT_AUTH_SECRET = os.getenv("CFDI_AUTH_SECRET") or "LaNT9KXAyIgtfHg61SdXK28os1ey1z0nKVkeqvxBXWXD0dOCdgraVq9tgEGOIUS3"
DEFAULT_AUTH_TTL_MINUTES = os.getenv("CFDI_AUTH_TTL_MINUTES") or 2880  # 2 days
DEFAULT_AUTH_PASSWORD_ITERATIONS = os.getenv("CFDI_AUTH_PASSWORD_ITERATIONS") or 390000 # Sube a 300k–600k en prod).
DEFAULT_TIMEOUT_SAT_SECONDS = os.getenv("CFDI_TIMEOUT_SAT_SECONDS") or 200

class Settings(BaseSettings):
    app_name: str = "CFDI API"
    auth_secret: str = DEFAULT_AUTH_SECRET
    auth_token_ttl_minutes: int = DEFAULT_AUTH_TTL_MINUTES
    auth_password_iterations: int = DEFAULT_AUTH_PASSWORD_ITERATIONS
    sat_password_secret: str = DEFAULT_SAT_PASSWORD_SECRET
    sat_cfdi_auth_url: str = (
        "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc"
    )
    sat_cfdi_solicitud_url: str = (
        "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc"
    )
    sat_cfdi_verificacion_url: str = (
        "https://cfdidescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc"
    )
    sat_cfdi_descarga_url: str = (
        "https://cfdidescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc"
    )
    sat_ret_auth_url: str = (
        "https://retendescargamasivasolicitud.clouda.sat.gob.mx/Autenticacion/Autenticacion.svc"
    )
    sat_ret_solicitud_url: str = (
        "https://retendescargamasivasolicitud.clouda.sat.gob.mx/SolicitaDescargaService.svc"
    )
    sat_ret_verificacion_url: str = (
        "https://retendescargamasivasolicitud.clouda.sat.gob.mx/VerificaSolicitudDescargaService.svc"
    )
    sat_ret_descarga_url: str = (
        "https://retendescargamasiva.clouda.sat.gob.mx/DescargaMasivaService.svc"
    )
    sat_timeout_seconds: int = DEFAULT_TIMEOUT_SAT_SECONDS
    sat_soap_action_descarga: str = (
        "http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"
    )


settings = Settings()
