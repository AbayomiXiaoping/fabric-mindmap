"""Runtime configuration management."""

from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the local runtime."""

    runtime_host: str = "127.0.0.1"
    runtime_port: int = 9720
    log_level: str = "INFO"
    sqlite_path: str = "lakehouse_intelligence.db"
    ai_enabled: bool = True
    ai_provider: Optional[str] = None
    fabric_tenant_id: Optional[str] = None
    metadata_lakehouse_id: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="LAKEHOUSE_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

