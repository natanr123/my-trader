import warnings

from pydantic import (
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


class Settings(BaseSettings):
    # If env params are not present will fall back to local-db
    model_config = SettingsConfigDict(
        env_file="dotenv/default/db.env",
        extra="ignore",
    )

    DB_SERVER: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
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

    def _check_default_secret(
        self, var_name: str, value: str | None, environment: str
    ) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if environment == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        # Import here to avoid circular dependency
        from app.core.config.config import settings as app_settings

        self._check_default_secret(
            "DB_PASSWORD", self.DB_PASSWORD, app_settings.ENVIRONMENT
        )
        return self


settings = Settings()  # type: ignore
