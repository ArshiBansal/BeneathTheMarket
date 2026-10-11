"""
Configuration package for Technology & Fintech Market Intelligence
and Regime Analyzer.

Exposes the most commonly used settings, ticker universe and constants
so that other modules can simply do:

    from config import settings, TICKERS, CATEGORIES
"""

from .settings import settings
from .tickers import TICKERS, CATEGORIES, get_tickers_by_category, get_primary_category
from .constants import (
    COLLECTIONS,
    INTERVALS,
    FORECAST_HORIZONS,
    ML_MODELS,
    DL_MODELS,
    REGIME_LABELS,
    FEATURE_GROUPS,
)

__all__ = [
    "settings",
    "TICKERS",
    "CATEGORIES",
    "get_tickers_by_category",
    "get_primary_category",
    "COLLECTIONS",
    "INTERVALS",
    "FORECAST_HORIZONS",
    "ML_MODELS",
    "DL_MODELS",
    "REGIME_LABELS",
    "FEATURE_GROUPS",
]
