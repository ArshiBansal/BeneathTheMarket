"""
Central application settings.

All values that may change between environments are loaded from
environment variables (see .env.example).  Defaults are sensible for
a local development setup that uses MongoDB Community Server on
localhost and does **not** use MongoDB Atlas.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from project root (one level above config/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    """Immutable-ish settings object.  Instantiate once via get_settings()."""

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    PROJECT_ROOT: Path = "C:\Users\hp\Documents\GitHub\BeneathTheMarket"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = DATA_DIR / "models"
    ML_MODELS_DIR: Path = MODELS_DIR / "ml"
    DL_MODELS_DIR: Path = MODELS_DIR / "dl"
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"

    # ------------------------------------------------------------------
    # MongoDB (LOCAL ONLY)
    # ------------------------------------------------------------------
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "tech_fintech_market_intel")
    MONGODB_USERNAME: str = os.getenv("MONGODB_USERNAME", "")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "")
    MONGODB_AUTH_SOURCE: str = os.getenv("MONGODB_AUTH_SOURCE", "admin")

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HOURLY_REFRESH_ENABLED: bool = (
        os.getenv("HOURLY_REFRESH_ENABLED", "true").lower() in ("1", "true", "yes")
    )
    DAILY_UPDATE_HOUR: int = int(os.getenv("DAILY_UPDATE_HOUR", "18"))

    # ------------------------------------------------------------------
    # Forecasting
    # ------------------------------------------------------------------
    DEFAULT_FORECAST_HORIZON: int = int(os.getenv("DEFAULT_FORECAST_HORIZON", "5"))
    MAX_FORECAST_HORIZON: int = int(os.getenv("MAX_FORECAST_HORIZON", "30"))

    # ------------------------------------------------------------------
    # Data retrieval defaults
    # ------------------------------------------------------------------
    DEFAULT_HISTORY_PERIOD: str = "5y"          # yfinance period string
    DEFAULT_INTERVAL: str = "1d"                # daily bars for persistence
    RECENT_INTERVAL: str = "1h"                 # for hourly refresh when supported
    REQUEST_TIMEOUT: int = 30                   # seconds
    MAX_RETRIES: int = 3

    def __post_init_paths(self) -> None:
        """Ensure critical directories exist."""
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
        """Kwargs suitable for pymongo.MongoClient."""
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
    """Return a cached Settings instance and create directories on first call."""
    s = Settings()
    s.__post_init_paths()
    return s


# Convenience singleton used throughout the project
settings = get_settings()