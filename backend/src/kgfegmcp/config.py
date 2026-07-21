"""This module contains the main configurations for the backend.

Any configurations added to backend/.env.local should be added to `BackendSettings` as
well.
"""

# Standard Library
from typing import Literal

# Third Party Library
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackendSettings(BaseSettings):
    """Pydantic settings for backend."""

    # Chat
    CHAT_ENV: Literal["dev", "prod", "local", "testing"] = "local"

    # Logging
    LOGGING_LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )


Settings: BackendSettings = BackendSettings()
