from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    VAULT_DATABASE_URL: str

    SECRET_KEY: str
    CLIENT_TOKEN_EXPIRE_MINUTES: int = 60

    ADMIN_SECRET_KEY: str
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 30

    ALGORITHM: str = "HS256"
    RSA_PRIVATE_KEY: str

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    CDN_BASE_URL: str = "https://cdn.nabegheha.com/download"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
