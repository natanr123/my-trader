from typing import Any

from pydantic import (
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.app_settings import app_settings


class AlpacaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"dotenv/{app_settings.ENVIRONMENT}/alpaca.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    ALPACA_NAME: str
    ALPACA_API_KEY: str
    ALPACA_SECRET_KEY: str
    ALPACA_PAPER: bool

    @computed_field
    def credentials(self) -> dict[str, Any]:
        return {
            "api-key": self.ALPACA_API_KEY,
            "secret-key": self.ALPACA_SECRET_KEY,
            "paper": self.ALPACA_PAPER,
        }


alpaca_settings = AlpacaSettings()

__all__ = ["alpaca_settings"]
