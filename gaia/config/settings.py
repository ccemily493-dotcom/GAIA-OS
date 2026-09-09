"""Centralized settings and configuration management for GAIA OS."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class GaiaSettings(BaseSettings):
    """Runtime configuration for GAIA OS."""

    model_config = SettingsConfigDict(
        env_prefix="GAIA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Persistence
    database_path: str = "data/gaia.db"

    # Model Provider ("rule_based", "openai", "fake")
    provider_type: str = "rule_based"
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"
    openai_model: str = "llama3.2"
    model_timeout_seconds: float = 30.0

    # Logging
    log_level: str = "INFO"

    @property
    def db_path_obj(self) -> Path:
        """Returns the database path as a Path object and ensures parent exists."""
        p = Path(self.database_path)
        if str(p) != ":memory:":
            p.parent.mkdir(parents=True, exist_ok=True)
        return p
