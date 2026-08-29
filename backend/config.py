from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class DbSettings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DATABASE: str
    POSTGRES_PASSWORD: str = " "
    DEBUG: bool = False
    REDIS_PORT: int
    REDIS_HOST: str

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    @property
    def POSTGRES_URL(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
        )

    def get_redis_url(self, db):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{db}"


db_settings = DbSettings()


class AppSettings(BaseSettings):
    SECRETS: str
    ALGORITHM: str
    ACCESS_TOKEN_EXP_TIME: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )


settings = AppSettings()


APP_DIR = Path(__file__).resolve().parent


class EmailSetttings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    TEMPLATE_FOLDER: Any = APP_DIR / "templates"

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )


mail_settings = EmailSetttings()


class PaymentSettings(BaseSettings):
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    PAYSTACK_BASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )


payment_settings = PaymentSettings()
