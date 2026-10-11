"""
High-level forecast generation.

Wraps any fitted model (ML, DL or baseline) and produces a standardised
ForecastResult that can be stored, displayed or further post-processed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """
    Standard container for a single forecast.

    Attributes
    ----------
    ticker : str
    horizon : int
        Forecast horizon in trading days.
    predicted_value : float
        Point forecast (return or price, depending on target).
    predicted_return : Optional[float]
        Explicit return forecast when the model targets returns.
    model_id : str
        Registry identifier of the model that produced the forecast.
    model_name : str
        Human-readable model name (e.g. "xgboost", "lstm").
    input_cutoff : datetime
        Timestamp of the last data point used as input.
    generated_at : datetime
        Wall-clock time when the forecast was created.
    lower_bound : Optional[float]
        Optional lower uncertainty bound (if the model supplies one).
    upper_bound : Optional[float]
        Optional upper uncertainty bound.
    metadata : dict
        Any extra information (feature snapshot, confidence, etc.).
    """
    ticker: str
    horizon: int
    predicted_value: float
    model_id: str
    model_name: str
    input_cutoff: datetime
    generated_at: datetime = field(default_factory=datetime.utcnow)
    predicted_return: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a MongoDB-friendly dictionary."""
        return {
            "ticker": self.ticker.upper(),
            "horizon": int(self.horizon),
            "predicted_value": float(self.predicted_value),
            "predicted_return": float(self.predicted_return)
            if self.predicted_return is not None
            else None,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "input_cutoff": self.input_cutoff,
            "generated_at": self.generated_at,
            "lower_bound": float(self.lower_bound)
            if self.lower_bound is not None
            else None,
            "upper_bound": float(self.upper_bound)
            if self.upper_bound is not None
            else None,
            "metadata": self.metadata,
        }


def generate_forecast(
    model: Any,
    X: pd.DataFrame,
    *,
    ticker: str,
    horizon: int = 1,
    model_id: str = "unknown",
    model_name: str = "unknown",
    target_is_return: bool = True,
    last_price: Optional[float] = None,
    predict_fn: Optional[callable] = None,
) -> ForecastResult:
    """
    Produce a ForecastResult from any fitted model.

    Parameters
    ----------
    model :
        Fitted estimator that implements `.predict(X)` or a custom
        callable supplied via `predict_fn`.
    X : pd.DataFrame
        Feature matrix whose **last row** is used as the prediction
        point (or the whole matrix for sequence models that expect
        a window).
    ticker : str
    horizon : int
    model_id, model_name : str
        Identifiers for registry / display.
    target_is_return : bool
        If True the model output is treated as a return; the caller
        may also supply `last_price` to convert to a price level.
    last_price : float, optional
        Used only when target_is_return=True and a price-level
        forecast is desired.
    predict_fn : callable, optional
        Custom prediction function `fn(model, X) -> array-like`.
        Useful for deep-learning trainers that expose their own
        `.predict` method.
    """
    ticker = ticker.upper()

    if predict_fn is not None:
        raw_pred = predict_fn(model, X)
    elif hasattr(model, "predict"):
        raw_pred = model.predict(X)
    else:
        raise TypeError(
            "model must implement .predict() or a predict_fn must be supplied"
        )

    # Normalise to a scalar (take the last prediction if a sequence was returned)
    pred_array = np.asarray(raw_pred).ravel()
    if len(pred_array) == 0:
        raise ValueError("Model returned an empty prediction")
    point_forecast = float(pred_array[-1])

    predicted_return = point_forecast if target_is_return else None
    predicted_value = point_forecast

    if target_is_return and last_price is not None:
        # Convert return forecast into an expected price level
        predicted_value = float(last_price * (1.0 + point_forecast))

    # Input cutoff = last timestamp present in X
    if isinstance(X.index, pd.DatetimeIndex) and len(X.index):
        input_cutoff = X.index.max().to_pydatetime()
    else:
        input_cutoff = datetime.utcnow()

    result = ForecastResult(
        ticker=ticker,
        horizon=horizon,
        predicted_value=predicted_value,
        predicted_return=predicted_return,
        model_id=model_id,
        model_name=model_name,
        input_cutoff=input_cutoff,
        metadata={
            "n_features": X.shape[1] if hasattr(X, "shape") else None,
            "target_is_return": target_is_return,
            "last_price_used": last_price,
        },
    )
    logger.debug(
        "Forecast generated: %s horizon=%d value=%.6f model=%s",
        ticker,
        horizon,
        predicted_value,
        model_name,
    )
    return result


def generate_forecasts_for_universe(
    model: Any,
    feature_dict: Dict[str, pd.DataFrame],
    *,
    horizon: int = 1,
    model_id: str = "unknown",
    model_name: str = "unknown",
    target_is_return: bool = True,
    price_dict: Optional[Dict[str, float]] = None,
    predict_fn: Optional[callable] = None,
) -> List[ForecastResult]:
    """
    Convenience helper that calls `generate_forecast` for every ticker
    present in `feature_dict`.
    """
    results = []
    price_dict = price_dict or {}
    for ticker, X in feature_dict.items():
        if X is None or X.empty:
            logger.warning("Skipping %s – empty feature matrix", ticker)
            continue
        try:
            fc = generate_forecast(
                model,
                X,
                ticker=ticker,
                horizon=horizon,
                model_id=model_id,
                model_name=model_name,
                target_is_return=target_is_return,
                last_price=price_dict.get(ticker),
                predict_fn=predict_fn,
            )
            results.append(fc)
        except Exception as exc:
            logger.warning("Forecast failed for %s: %s", ticker, exc)
    return results