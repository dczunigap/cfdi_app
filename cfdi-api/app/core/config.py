from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CFDI API"


settings = Settings()
