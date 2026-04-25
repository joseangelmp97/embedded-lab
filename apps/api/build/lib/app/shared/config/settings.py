from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Embedded Lab API"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./embedded_lab_dev.db"
    auth_jwt_secret_key: str = "change-me-in-env"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
