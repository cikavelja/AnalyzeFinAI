"""Application configuration via pydantic-settings.

All settings are read from environment variables (or a .env file).
Import the ``settings`` singleton — do not instantiate ``Settings`` directly.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object populated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── LLM ────────────────────────────────────────────────────────────────
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    # ── Conversion ─────────────────────────────────────────────────────────
    # Supported values: "local" | "markitdown" | "mcp"
    conversion_mode: str = Field(default="markitdown", alias="CONVERSION_MODE")
    mcp_endpoint: str = Field(
        default="http://localhost:3001/convert", alias="MCP_ENDPOINT"
    )

    # ── Logging ────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── Audit ──────────────────────────────────────────────────────────────
    audit_log_path: str = Field(default="data/audit.jsonl", alias="AUDIT_LOG_PATH")

    # ── Safety ─────────────────────────────────────────────────────────────
    local_only_mode: bool = Field(default=False, alias="LOCAL_ONLY_MODE")


# Singleton — import this everywhere instead of instantiating Settings()
settings = Settings()
