from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # a rejected setting is often a secret: keep its value out of the error, which ends up in the logs
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    # No default on purpose: the app must not start with a key someone could guess.
    SECRET_KEY: str = Field(min_length=32)
    DATABASE_URL: str = "sqlite:///./inventory.db"
    # The first admin, created at startup if no user exists yet. People who register are staff.
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    TOKEN_MINUTES: int = 60
    # Where picture files are kept. With "s3", boto3 finds the credentials and region itself.
    PICTURE_STORAGE: Literal["db", "s3"] = "db"
    PICTURE_BUCKET: str = ""
    # How many of our own proxies stand in front of the app (see ratelimit.client_address). 0: none.
    TRUSTED_PROXIES: int = Field(default=0, ge=0)
    LOGIN_ATTEMPTS: int = 5  # wrong passwords for one account from one address, per 15 minutes
    LOGIN_ATTEMPTS_PER_ADDRESS: int = 20  # across all accounts, per 15 minutes
    REGISTRATIONS_PER_HOUR: int = 10  # per address
    # Cloudflare Turnstile on sign-up. Both or neither.
    TURNSTILE_SITE_KEY: str = ""
    TURNSTILE_SECRET_KEY: str = ""

    @model_validator(mode="after")
    def bucket_named(self):
        if self.PICTURE_STORAGE == "s3" and not self.PICTURE_BUCKET:
            raise ValueError("PICTURE_STORAGE=s3 needs PICTURE_BUCKET")
        return self

    @model_validator(mode="after")
    def both_turnstile_keys(self):
        if bool(self.TURNSTILE_SITE_KEY) != bool(self.TURNSTILE_SECRET_KEY):
            raise ValueError("Set both TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY, or neither")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
