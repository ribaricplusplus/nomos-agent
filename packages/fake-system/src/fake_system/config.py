"""Runtime configuration, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # SQLAlchemy URL. Uses the psycopg (v3) driver.
    database_url: str = "postgresql+psycopg://nomos:nomos@localhost:5432/fake_system"

    # Dashboard (FastAPI / uvicorn)
    web_host: str = "0.0.0.0"
    web_port: int = 8000

    # MCP server (streamable HTTP)
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8765


@lru_cache
def get_settings() -> Settings:
    return Settings()
