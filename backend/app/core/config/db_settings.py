import os
from pydantic import (
    PostgresDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    # If env params are not present will fall back to local-db
    model_config = SettingsConfigDict(
        env_file= 'dotenv/default/db.env',
        extra="ignore",
    )

    DB_SERVER: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_DSN: str # For Oracle TNS connection string

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # PostgreSQL connection
        return str(PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_SERVER,
            port=self.DB_PORT,
            path=self.DB_NAME,
        ))

settings = Settings()  # type: ignore
