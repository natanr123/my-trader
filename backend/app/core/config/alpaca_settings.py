import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

class AlpacaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=".alpaca.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    ALPACA_NAME: str
    ALPACA_API_KEY: str
    ALPACA_SECRET_KEY: str
    ALPACA_PAPER: bool

    @computed_field
    @property
    def credentials(self) -> dict:
        return {
            'api-key': self.ALPACA_API_KEY,
            'secret-key': self.ALPACA_SECRET_KEY,
            'paper': self.ALPACA_PAPER,
        }


alpaca_settings = AlpacaSettings()
