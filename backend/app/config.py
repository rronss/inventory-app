from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # No default on purpose: the app must not start with a key someone could guess.
    SECRET_KEY: str = Field(min_length=32)
    DATABASE_URL: str = "sqlite:///./inventory.db"
    # The first admin, created at startup if no user exists yet. People who register are staff.
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    TOKEN_MINUTES: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
