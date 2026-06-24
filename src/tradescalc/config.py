"""Application configuration and settings."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "TradesCalc API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="TRADESCALC_ENV")
    debug: bool = False

    # Security — comma-separated list to support multiple RapidAPI listings
    rapidapi_proxy_secret: str = Field(default="", alias="RAPIDAPI_PROXY_SECRET")
    api_key_salt: str = Field(default="tradescalc-dev-salt", alias="TRADESCALC_API_KEY_SALT")

    # Rate Limiting
    free_tier_rpm: int = 10  # requests per minute
    pro_tier_rpm: int = 100

    # Data
    data_dir: Path = Path(__file__).parent / "data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
