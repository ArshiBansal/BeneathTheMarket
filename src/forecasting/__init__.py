"""
Forecasting package – high-level prediction helpers and post-processing.

Public API
----------
from src.forecasting import (
    ForecastResult,
    generate_forecast,
    format_forecast_for_storage,
    attach_uncertainty_notes,
)
"""

from .predictor import ForecastResult, generate_forecast
from .postprocess import format_forecast_for_storage, attach_uncertainty_notes

__all__ = [
    "ForecastResult",
    "generate_forecast",
    "format_forecast_for_storage",
    "attach_uncertainty_notes",
]