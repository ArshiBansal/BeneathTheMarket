"""
Project-wide constants that should not change at runtime.

These values are used for collection names, model registries,
feature groups, regime definitions, etc.
"""

from __future__ import annotations

from typing import Dict, List

# MongoDB collection names (must match src/db/collections.py)
COLLECTIONS: Dict[str, str] = {
    "market_data": "market_data",
    "company_metadata": "company_metadata",
    "analysis_results": "analysis_results",
    "predictions": "predictions",
    "model_evaluations": "model_evaluations",
    "refresh_status": "refresh_status",
}

# Supported yfinance intervals
INTERVALS: Dict[str, str] = {
    "daily": "1d",
    "hourly": "1h",
    "weekly": "1wk",
    "monthly": "1mo",
}

# Forecast horizons (trading days)
FORECAST_HORIZONS: List[int] = [1, 5, 10, 21]   # 1-day, 1-week, 2-week, ~1-month

# Machine-learning algorithms to evaluate (>3 required)
ML_MODELS: List[str] = [
    "ridge",
    "random_forest",
    "xgboost",
    "lightgbm",
    "catboost",
]

# Deep-learning approaches to evaluate (>3 required)
DL_MODELS: List[str] = [
    "lstm",
    "gru",
    "tcn",          # Temporal Convolutional Network
    "transformer",  # simple time-series transformer
]

# Market-regime labels (operational definitions)
REGIME_LABELS: Dict[str, str] = {
    "bull": "upward-trending",
    "bear": "downward-trending",
    "sideways": "range-bound",
    "high_vol": "high-volatility",
}

# Feature groups used in feature engineering
FEATURE_GROUPS: Dict[str, List[str]] = {
    "returns": [
        "ret_1d",
        "ret_5d",
        "ret_21d",
        "log_ret_1d",
    ],
    "volatility": [
        "vol_5d",
        "vol_21d",
        "vol_63d",
        "realized_vol",
    ],
    "drawdown": [
        "max_drawdown_21d",
        "max_drawdown_63d",
        "drawdown_from_peak",
    ],
    "volume": [
        "volume_change_1d",
        "volume_sma_ratio_5d",
        "volume_sma_ratio_21d",
    ],
    "trend": [
        "sma_5",
        "sma_21",
        "sma_63",
        "ema_12",
        "ema_26",
        "macd",
        "rsi_14",
    ],
    "cross_company": [
        "corr_market_21d",
        "beta_market_63d",
        "relative_strength_21d",
    ],
}

# Evaluation metrics (for documentation / selection)
REGRESSION_METRICS: List[str] = [
    "mae",
    "rmse",
    "mape",
    "r2",
]

CLASSIFICATION_METRICS: List[str] = [
    "accuracy",
    "precision_macro",
    "recall_macro",
    "f1_macro",
    "balanced_accuracy",
]

# Default random seed for reproducibility
RANDOM_SEED: int = 42