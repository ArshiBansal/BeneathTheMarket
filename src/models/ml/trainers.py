"""
Training & evaluation loop for classical ML models.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.models.evaluation import (
    chronological_split,
    evaluate_regression,
    evaluate_classification,
)
from src.models.registry import ModelRegistry
from .models import get_ml_model, ML_MODEL_NAMES

logger = logging.getLogger(__name__)


class MLTrainer:
    """
    End-to-end trainer for a single classical ML model.

    Responsibilities
    ----------------
    - chronological train/val/test split
    - optional scaling (fit on train only)
    - fit + predict
    - metric computation
    - optional registration in ModelRegistry
    """

    def __init__(
        self,
        model_name: str,
        *,
        task: str = "regression",
        scale_features: bool = True,
        random_state: int = 42,
        model_kwargs: Optional[Dict[str, Any]] = None,
    ):
        if model_name not in ML_MODEL_NAMES:
            raise ValueError(f"model_name must be one of {ML_MODEL_NAMES}")
        self.model_name = model_name
        self.task = task
        self.scale_features = scale_features
        self.random_state = random_state
        self.model_kwargs = model_kwargs or {}
        self.model = None
        self.scaler = None
        self.metrics_: Dict[str, float] = {}
        self.feature_cols_: List[str] = []

    def fit_evaluate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        gap: int = 0,
        register: bool = False,
        target_name: str = "ret_1d",
        horizon: int = 1,
    ) -> Dict[str, Any]:
        """
        Full train → validate → test cycle.

        Returns a dictionary containing metrics and metadata.
        """
        assert len(X) == len(y), "X and y must have the same length"
        self.feature_cols_ = list(X.columns)

        split = chronological_split(
            len(X),
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            gap=gap,
        )

        X_train, y_train = X.iloc[split.train_idx], y.iloc[split.train_idx]
        X_val, y_val = X.iloc[split.val_idx], y.iloc[split.val_idx]
        X_test, y_test = X.iloc[split.test_idx], y.iloc[split.test_idx]

        # Scaling – fit only on training data
        if self.scale_features:
            self.scaler = StandardScaler()
            X_train = pd.DataFrame(
                self.scaler.fit_transform(X_train),
                index=X_train.index,
                columns=X_train.columns,
            )
            if len(X_val):
                X_val = pd.DataFrame(
                    self.scaler.transform(X_val),
                    index=X_val.index,
                    columns=X_val.columns,
                )
            X_test = pd.DataFrame(
                self.scaler.transform(X_test),
                index=X_test.index,
                columns=X_test.columns,
            )

        # Instantiate & fit
        self.model = get_ml_model(
            self.model_name,
            task=self.task,
            random_state=self.random_state,
            **self.model_kwargs,
        )
        self.model.fit(X_train, y_train)

        # Predictions
        y_pred_test = self.model.predict(X_test)
        y_pred_val = self.model.predict(X_val) if len(X_val) else None

        # Metrics
        if self.task == "regression":
            self.metrics_ = evaluate_regression(y_test, y_pred_test, prefix="test_")
            if y_pred_val is not None and len(y_val):
                val_metrics = evaluate_regression(y_val, y_pred_val, prefix="val_")
                self.metrics_.update(val_metrics)
        else:
            self.metrics_ = evaluate_classification(y_test, y_pred_test, prefix="test_")
            if y_pred_val is not None and len(y_val):
                val_metrics = evaluate_classification(y_val, y_pred_val, prefix="val_")
                self.metrics_.update(val_metrics)

        result = {
            "model_name": self.model_name,
            "task": self.task,
            "metrics": self.metrics_,
            "n_train": len(X_train),
            "n_val": len(X_val),
            "n_test": len(X_test),
            "feature_cols": self.feature_cols_,
        }

        if register:
            registry = ModelRegistry(model_type="ml")
            model_id = registry.register(
                self.model,
                name=self.model_name,
                metrics=self.metrics_,
                params=self.model_kwargs,
                feature_cols=self.feature_cols_,
                target=target_name,
                horizon=horizon,
                train_end=str(X_train.index.max()) if hasattr(X_train.index, "max") else None,
                test_start=str(X_test.index.min()) if hasattr(X_test.index, "min") else None,
                test_end=str(X_test.index.max()) if hasattr(X_test.index, "max") else None,
            )
            result["model_id"] = model_id

        logger.info(
            "MLTrainer [%s] test_rmse/acc=%.5f",
            self.model_name,
            self.metrics_.get("test_rmse") or self.metrics_.get("test_accuracy", float("nan")),
        )
        return result

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model has not been fitted yet")
        if self.scale_features and self.scaler is not None:
            X = pd.DataFrame(
                self.scaler.transform(X),
                index=X.index,
                columns=X.columns,
            )
        return self.model.predict(X)