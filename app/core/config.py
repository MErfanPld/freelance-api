from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Freelance Project Manager"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./freelance_manager.db"

    jwt_secret_key: str = Field(
        default="change-this-secret-in-production",
    )
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    encryption_key: str = Field(
        default="change-this-fernet-key-in-production",
    )

    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
