import warnings

from pydantic import (
    PostgresDsn,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from app.core.config.app_settings import app_settings


class DbSettings(BaseSettings):
    # Dynamically select env file based on ENVIRONMENT variable
    model_config = SettingsConfigDict(
        env_file=f"dotenv/{app_settings.ENVIRONMENT}/db.env",
        extra="ignore",
    )

    DB_SERVER: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    def sqlalchemy_database_uri(self) -> str:
        # PostgreSQL connection using psycopg (version 3)
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_SERVER,
                port=self.DB_PORT,
                path=self.DB_NAME,
            )
        )


db_settings = DbSettings()

__all__ = ["db_settings"]
