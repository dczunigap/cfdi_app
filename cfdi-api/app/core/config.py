import os

from pydantic_settings import BaseSettings


DEFAULT_SAT_PASSWORD_SECRET = os.getenv("SAT_PASSWORD_SECRET") or "CjtwIZ6dGe5cwHgrLpW-YowE56KQYd9Uc9onVAO3WCw="


class Settings(BaseSettings):
    app_name: str = "CFDI API"
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
    sat_timeout_seconds: int = 200
    sat_soap_action_descarga: str = (
        "http://DescargaMasivaTerceros.sat.gob.mx/IDescargaMasivaTercerosService/Descargar"
    )


settings = Settings()
