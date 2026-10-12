"""
Model loading and inference helpers for the Streamlit app.

Loads artefacts registered by the notebooks / training scripts.
Handles missing artefacts gracefully (returns None / empty metrics).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import settings
from src.db.model_evaluations import get_model_evaluations, get_best_evaluation
from src.db.predictions import get_predictions, get_latest_prediction, save_prediction
from src.models.registry import ModelRegistry
from src.forecasting.predictor import generate_forecast, ForecastResult
from src.forecasting.postprocess import (
    format_forecast_for_storage,
    attach_uncertainty_notes,
)

logger = logging.getLogger(__name__)


class ModelService:
    """Inference-side access to trained models and stored predictions."""

    def __init__(self, model_type: str = "ml"):
        self.model_type = model_type
        self.registry = ModelRegistry(model_type=model_type)

    # ------------------------------------------------------------------
    # Registry / evaluation queries
    # ------------------------------------------------------------------
    def list_models(self, name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            return self.registry.list_models(name=name, limit=limit)
        except Exception as exc:
            logger.warning("list_models failed: %s", exc)
            return []

    def best_model(
        self,
        metric: str = "test_rmse",
        higher_is_better: bool = False,
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            return self.registry.best_model(
                metric=metric.replace("test_", "") if metric.startswith("test_") else metric,
                higher_is_better=higher_is_better,
                name=name,
            )
        except Exception as exc:
            logger.warning("best_model failed: %s", exc)
            return None

    def get_evaluations(
        self,
        model_id: Optional[str] = None,
        model_type: Optional[str] = None,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        try:
            return get_model_evaluations(
                model_id=model_id,
                model_type=model_type or self.model_type,
                limit=limit,
            )
        except Exception as exc:
            logger.warning("get_evaluations failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Load artefact
    # ------------------------------------------------------------------
    def load_model(self, model_id: str) -> Any:
        """
        Load a registered model artefact.
        Returns None if the artefact is missing (UI should handle gracefully).
        """
        try:
            return self.registry.load(model_id)
        except FileNotFoundError:
            logger.warning("Model artefact not found: %s", model_id)
            return None
        except Exception as exc:
            logger.warning("load_model failed for %s: %s", model_id, exc)
            return None

    # ------------------------------------------------------------------
    # Predictions store
    # ------------------------------------------------------------------
    def list_predictions(
        self,
        ticker: Optional[str] = None,
        horizon: Optional[int] = None,
        model_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        try:
            return get_predictions(
                ticker=ticker, horizon=horizon, model_id=model_id, limit=limit
            )
        except Exception as exc:
            logger.warning("list_predictions failed: %s", exc)
            return []

    def latest_prediction(
        self,
        ticker: str,
        horizon: int,
        model_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            return get_latest_prediction(ticker, horizon, model_id=model_id)
        except Exception as exc:
            logger.warning("latest_prediction failed: %s", exc)
            return None

    def save_forecast(self, result: ForecastResult) -> str:
        """Attach uncertainty notes and persist."""
        result = attach_uncertainty_notes(result)
        doc = format_forecast_for_storage(result)
        return save_prediction(doc)

    # ------------------------------------------------------------------
    # Simple inference helper (classical ML artefacts)
    # ------------------------------------------------------------------
    def predict_with_ml_artefact(
        self,
        model_id: str,
        features: pd.DataFrame,
        *,
        ticker: str,
        horizon: int = 5,
        target_is_return: bool = True,
        last_price: Optional[float] = None,
    ) -> Optional[ForecastResult]:
        """
        Run a registered sklearn-style model on a feature row/matrix.
        Returns None when the artefact cannot be loaded.
        """
        model = self.load_model(model_id)
        if model is None:
            return None
        meta = self.registry.get_metadata(model_id) or {}
        try:
            fc = generate_forecast(
                model,
                features,
                ticker=ticker,
                horizon=horizon,
                model_id=model_id,
                model_name=meta.get("name", model_id),
                target_is_return=target_is_return,
                last_price=last_price,
            )
            return attach_uncertainty_notes(fc)
        except Exception as exc:
            logger.warning("predict_with_ml_artefact failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Leaderboard helper for UI
    # ------------------------------------------------------------------
    @staticmethod
    def load_leaderboard(limit: int = 20) -> pd.DataFrame:
        path = settings.PROCESSED_DATA_DIR / "model_leaderboard.csv"
        if not path.exists():
            return pd.DataFrame()
        try:
            df = pd.read_csv(path)
            return df.head(limit)
        except Exception as exc:
            logger.warning("load_leaderboard failed: %s", exc)
            return pd.DataFrame()