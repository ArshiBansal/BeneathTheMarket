"""
Factory for the classical ML algorithms that must be evaluated
(>3 required by the project proposal).

Supported names
---------------
ridge, random_forest, xgboost, lightgbm, catboost
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

logger = logging.getLogger(__name__)

ML_MODEL_NAMES: List[str] = [
    "ridge",
    "random_forest",
    "xgboost",
    "lightgbm",
    "catboost",
]


def get_ml_model(
    name: str,
    *,
    task: str = "regression",
    random_state: int = 42,
    **kwargs,
) -> Any:
    """
    Return an unfitted sklearn-compatible estimator.

    Parameters
    ----------
    name : str
        One of ML_MODEL_NAMES.
    task : str
        'regression' or 'classification'.
    random_state : int
        Reproducibility seed.
    **kwargs
        Extra hyper-parameters forwarded to the constructor.
    """
    name = name.lower().strip()
    if name not in ML_MODEL_NAMES:
        raise ValueError(f"Unknown ML model '{name}'. Choose from {ML_MODEL_NAMES}")

    if task not in ("regression", "classification"):
        raise ValueError("task must be 'regression' or 'classification'")

    if name == "ridge":
        if task == "classification":
            from sklearn.linear_model import LogisticRegression
            return LogisticRegression(
                max_iter=1000,
                random_state=random_state,
                **kwargs,
            )
        return Ridge(random_state=random_state, **kwargs)

    if name == "random_forest":
        cls = RandomForestClassifier if task == "classification" else RandomForestRegressor
        return cls(
            n_estimators=kwargs.pop("n_estimators", 200),
            max_depth=kwargs.pop("max_depth", 8),
            n_jobs=-1,
            random_state=random_state,
            **kwargs,
        )

    if name == "xgboost":
        try:
            from xgboost import XGBRegressor, XGBClassifier
        except ImportError as exc:
            raise ImportError("xgboost is required – add it to requirements.txt") from exc
        cls = XGBClassifier if task == "classification" else XGBRegressor
        return cls(
            n_estimators=kwargs.pop("n_estimators", 300),
            max_depth=kwargs.pop("max_depth", 6),
            learning_rate=kwargs.pop("learning_rate", 0.05),
            subsample=kwargs.pop("subsample", 0.8),
            colsample_bytree=kwargs.pop("colsample_bytree", 0.8),
            random_state=random_state,
            n_jobs=-1,
            verbosity=0,
            **kwargs,
        )

    if name == "lightgbm":
        try:
            from lightgbm import LGBMRegressor, LGBMClassifier
        except ImportError as exc:
            raise ImportError("lightgbm is required – add it to requirements.txt") from exc
        cls = LGBMClassifier if task == "classification" else LGBMRegressor
        return cls(
            n_estimators=kwargs.pop("n_estimators", 300),
            max_depth=kwargs.pop("max_depth", 6),
            learning_rate=kwargs.pop("learning_rate", 0.05),
            subsample=kwargs.pop("subsample", 0.8),
            colsample_bytree=kwargs.pop("colsample_bytree", 0.8),
            random_state=random_state,
            n_jobs=-1,
            verbose=-1,
            **kwargs,
        )

    if name == "catboost":
        try:
            from catboost import CatBoostRegressor, CatBoostClassifier
        except ImportError as exc:
            raise ImportError("catboost is required – add it to requirements.txt") from exc
        cls = CatBoostClassifier if task == "classification" else CatBoostRegressor
        return cls(
            iterations=kwargs.pop("iterations", 300),
            depth=kwargs.pop("depth", 6),
            learning_rate=kwargs.pop("learning_rate", 0.05),
            random_seed=random_state,
            verbose=False,
            **kwargs,
        )

    raise RuntimeError(f"Unhandled model name: {name}")