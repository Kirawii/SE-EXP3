from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_cors_origins: list[str] = ["http://localhost:5173"]

    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    jwt_secret: str = "dev-only-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_hours: int = 24

    login_rate_limit: int = 5
    login_rate_window_seconds: int = 60

    landmark_auto_approve: bool = True
    default_geo_key: str = "geo:landmarks"

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
