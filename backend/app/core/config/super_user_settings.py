import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    computed_field,
    model_validator,
)

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self
from app.core.config.app_settings import app_settings




class SuperUserSettings(BaseSettings):
    mmodel_config = SettingsConfigDict(
        env_file=f"dotenv/{app_settings.ENVIRONMENT}/super_user.env",
        extra="ignore",
    )




super_user_settings = SuperUserSettings()  # type: ignore

__all__ = ["super_user_settings"]
