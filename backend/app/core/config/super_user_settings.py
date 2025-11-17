
from pydantic import (
    EmailStr,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.app_settings import app_settings


class SuperUserSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f"dotenv/{app_settings.ENVIRONMENT}/super_user.env",
        extra="ignore",
    )

    FIRST_SUPER_USER_EMAIL: EmailStr
    FIRST_SUPER_USER_PASSWORD: str




super_user_settings = SuperUserSettings()

__all__ = ["super_user_settings"]
