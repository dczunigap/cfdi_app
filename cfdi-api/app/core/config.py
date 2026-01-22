from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CFDI API"
    mi_rfc: str = "ZUPD8402022A2"


settings = Settings()
