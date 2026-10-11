"""
Simple baseline models used for fair comparison.

Every forecasting experiment must be evaluated against at least one
of these baselines (project requirement).
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin

logger = logging.getLogger(__name__)


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """
    Naive persistence / last-value baseline.

    Predicts that the next return (or price) will be identical to the
    most recent observed value.  Horizon is handled by repeating the
    last observation.
    """

    def __init__(self, horizon: int = 1):
        self.horizon = horizon
        self.last_value_: Optional[float] = None

    def fit(self, X, y):
        """
        Store the last target value observed in the training set.
        X is ignored (kept only for sklearn API compatibility).
        """
        y = np.asarray(y).ravel()
        if len(y) == 0:
            raise ValueError("y must contain at least one observation")
        self.last_value_ = float(y[-1])
        return self

    def predict(self, X):
        if self.last_value_ is None:
            raise RuntimeError("Model has not been fitted yet")
        n = len(X) if hasattr(X, "__len__") else 1
        return np.full(n, self.last_value_)

    def __repr__(self) -> str:
        return f"PersistenceBaseline(horizon={self.horizon})"


class HistoricalAverageBaseline(BaseEstimator, RegressorMixin):
    """
    Predict the historical mean of the target (computed on the
    training window only – no leakage).
    """

    def __init__(self, horizon: int = 1):
        self.horizon = horizon
        self.mean_: Optional[float] = None

    def fit(self, X, y):
        y = np.asarray(y).ravel()
        if len(y) == 0:
            raise ValueError("y must contain at least one observation")
        self.mean_ = float(np.nanmean(y))
        return self

    def predict(self, X):
        if self.mean_ is None:
            raise RuntimeError("Model has not been fitted yet")
        n = len(X) if hasattr(X, "__len__") else 1
        return np.full(n, self.mean_)

    def __repr__(self) -> str:
        return f"HistoricalAverageBaseline(horizon={self.horizon})"


class SeasonalNaiveBaseline(BaseEstimator, RegressorMixin):
    """
    Seasonal naïve baseline: predict the value from the same
    weekday / period one season ago.

    For daily data a season of 5 (trading week) or 21 (approx. month)
    is typical.  Falls back to persistence when not enough history.
    """

    def __init__(self, season_length: int = 5, horizon: int = 1):
        self.season_length = season_length
        self.horizon = horizon
        self.history_: Optional[np.ndarray] = None

    def fit(self, X, y):
        y = np.asarray(y).ravel()
        self.history_ = y.copy()
        return self

    def predict(self, X):
        if self.history_ is None or len(self.history_) == 0:
            raise RuntimeError("Model has not been fitted yet")
        n = len(X) if hasattr(X, "__len__") else 1
        preds = []
        hist = list(self.history_)
        for _ in range(n):
            if len(hist) >= self.season_length:
                preds.append(hist[-self.season_length])
            else:
                preds.append(hist[-1])
            # append prediction so multi-step stays consistent
            hist.append(preds[-1])
        return np.asarray(preds)

    def __repr__(self) -> str:
        return (
            f"SeasonalNaiveBaseline(season_length={self.season_length}, "
            f"horizon={self.horizon})"
        )