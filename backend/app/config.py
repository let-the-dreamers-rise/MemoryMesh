from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for local and hackathon demo environments."""

    vectorai_url: str = "localhost:50051"
    memorymesh_collection: str = "memorymesh_thoughts"
    memorymesh_embedding_mode: str = "auto"
    memorymesh_enable_actian: bool = True
    memorymesh_cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.memorymesh_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

