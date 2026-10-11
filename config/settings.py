# config/settings.py
"""
Central application settings – hardened against dirty .env values.
Works with local MongoDB only (no Atlas).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Project root = folder that contains the "config" package
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _safe_int(value: str | None, default: int) -> int:
    """
    Parse an integer from an environment variable that may contain
    trailing comments or extra whitespace.
    Examples that now work:
        "18"
        "18          # 24-hour format, local time"
        "  5  # days"
    """
    if value is None:
        return default
    # Keep only the part before a comment and strip whitespace
    cleaned = re.split(r"[#;]", value, maxsplit=1)[0].strip()
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return default


def _safe_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """Settings loaded once and cached."""

    # Paths (always Path objects)
    PROJECT_ROOT: Path = _PROJECT_ROOT
    DATA_DIR: Path = _PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = DATA_DIR / "models"
    ML_MODELS_DIR: Path = MODELS_DIR / "ml"
    DL_MODELS_DIR: Path = MODELS_DIR / "dl"
    REPORTS_DIR: Path = _PROJECT_ROOT / "reports"
    LOGS_DIR: Path = _PROJECT_ROOT / "logs"

    # MongoDB (local only)
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017").strip()
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "tech_fintech_market_intel").strip()
    MONGODB_USERNAME: str = os.getenv("MONGODB_USERNAME", "").strip()
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "").strip()
    MONGODB_AUTH_SOURCE: str = os.getenv("MONGODB_AUTH_SOURCE", "admin").strip()

    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development").strip()
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip()
    HOURLY_REFRESH_ENABLED: bool = _safe_bool(os.getenv("HOURLY_REFRESH_ENABLED"), True)
    DAILY_UPDATE_HOUR: int = _safe_int(os.getenv("DAILY_UPDATE_HOUR"), 18)

    # Forecasting
    DEFAULT_FORECAST_HORIZON: int = _safe_int(os.getenv("DEFAULT_FORECAST_HORIZON"), 5)
    MAX_FORECAST_HORIZON: int = _safe_int(os.getenv("MAX_FORECAST_HORIZON"), 30)

    # Data retrieval defaults
    DEFAULT_HISTORY_PERIOD: str = "5y"
    DEFAULT_INTERVAL: str = "1d"
    RECENT_INTERVAL: str = "1h"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    def _ensure_dirs(self) -> None:
        for path in (
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.ML_MODELS_DIR,
            self.DL_MODELS_DIR,
            self.REPORTS_DIR,
            self.LOGS_DIR,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    @property
    def mongo_connection_kwargs(self) -> dict:
        kwargs = {
            "host": self.MONGODB_URI,
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
        }
        if self.MONGODB_USERNAME and self.MONGODB_PASSWORD:
            kwargs["username"] = self.MONGODB_USERNAME
            kwargs["password"] = self.MONGODB_PASSWORD
            kwargs["authSource"] = self.MONGODB_AUTH_SOURCE
        return kwargs


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s._ensure_dirs()
    return s


settings = get_settings()