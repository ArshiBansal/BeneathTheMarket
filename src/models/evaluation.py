"""
Chronological evaluation utilities – no random shuffling, no leakage.

All splits respect time order.  Scaling / feature selection that need
fitting must be performed only on the training portion (caller responsibility).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    confusion_matrix,
    silhouette_score,
)

logger = logging.getLogger(__name__)

# Split helpers

@dataclass
class ChronologicalSplit:
    """Container for a single train / validation / test split."""
    train_idx: np.ndarray
    val_idx: np.ndarray
    test_idx: np.ndarray
    train_end: Any = None
    val_end: Any = None
    test_end: Any = None


def chronological_split(
    n_samples: int,
    *,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    gap: int = 0,
) -> ChronologicalSplit:
    """
    Pure index-based chronological split.

    Parameters
    ----------
    n_samples : int
    train_ratio, val_ratio, test_ratio : float
        Must sum to ≈ 1.0.
    gap : int
        Number of samples left unused between train/val and val/test
        (embargo to reduce leakage from overlapping windows).
    """
    if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0, atol=0.01):
        raise ValueError("train_ratio + val_ratio + test_ratio must sum to 1.0")

    train_end = int(n_samples * train_ratio)
    val_end = train_end + int(n_samples * val_ratio)

    train_idx = np.arange(0, train_end)
    val_idx = np.arange(train_end + gap, val_end)
    test_idx = np.arange(val_end + gap, n_samples)

    return ChronologicalSplit(
        train_idx=train_idx,
        val_idx=val_idx,
        test_idx=test_idx,
        train_end=train_end,
        val_end=val_end,
        test_end=n_samples,
    )


def walk_forward_split(
    n_samples: int,
    *,
    n_splits: int = 5,
    train_min_size: int = 252,
    test_size: int = 63,
    gap: int = 0,
) -> List[ChronologicalSplit]:
    """
    Expanding-window walk-forward splits.

    Each fold uses all data up to the start of the test window as training
    (no separate validation inside the fold – caller may carve one out).
    """
    splits = []
    start = train_min_size
    while start + test_size <= n_samples and len(splits) < n_splits:
        train_idx = np.arange(0, start)
        test_idx = np.arange(start + gap, start + gap + test_size)
        splits.append(
            ChronologicalSplit(
                train_idx=train_idx,
                val_idx=np.array([], dtype=int),  # optional
                test_idx=test_idx,
                train_end=start,
                test_end=start + gap + test_size,
            )
        )
        start += test_size
    return splits

# Metric helpers

def evaluate_regression(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series],
    *,
    prefix: str = "",
) -> Dict[str, float]:
    """
    Standard regression metrics + a few finance-friendly extras.
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    # Align lengths (safety)
    n = min(len(y_true), len(y_pred))
    y_true, y_pred = y_true[:n], y_pred[:n]

    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred) if n > 1 else np.nan

    # MAPE – avoid division by zero
    mask = np.abs(y_true) > 1e-8
    mape = (
        float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))) * 100
        if mask.any()
        else np.nan
    )

    # Directional accuracy (sign of return)
    dir_acc = float(np.mean(np.sign(y_true) == np.sign(y_pred))) if n > 0 else np.nan

    metrics = {
        f"{prefix}mae": float(mae),
        f"{prefix}rmse": rmse,
        f"{prefix}r2": float(r2),
        f"{prefix}mape": mape,
        f"{prefix}directional_accuracy": dir_acc,
        f"{prefix}n_samples": float(n),
    }
    return metrics


def evaluate_classification(
    y_true: Union[np.ndarray, pd.Series],
    y_pred: Union[np.ndarray, pd.Series],
    *,
    average: str = "macro",
    prefix: str = "",
) -> Dict[str, Any]:
    """
    Classification metrics + confusion matrix.
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()

    metrics = {
        f"{prefix}accuracy": float(accuracy_score(y_true, y_pred)),
        f"{prefix}balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        f"{prefix}precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),
        f"{prefix}recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),
        f"{prefix}f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
        f"{prefix}n_samples": float(len(y_true)),
        f"{prefix}confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    return metrics


def evaluate_clustering(
    X: np.ndarray,
    labels: np.ndarray,
    *,
    prefix: str = "",
) -> Dict[str, float]:
    """
    Basic internal cluster-quality metrics.
    """
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    sil = float(silhouette_score(X, labels)) if n_clusters > 1 else np.nan
    return {
        f"{prefix}silhouette": sil,
        f"{prefix}n_clusters": float(n_clusters),
        f"{prefix}n_samples": float(len(labels)),
    }

# Convenience runner

def run_baseline_comparison(
    y_train: np.ndarray,
    y_test: np.ndarray,
    X_test: Optional[np.ndarray] = None,
    horizon: int = 1,
) -> Dict[str, Dict[str, float]]:
    """
    Fit the three baselines on y_train and evaluate on y_test.
    Returns a nested dict keyed by baseline name.
    """
    from .baselines import (
        PersistenceBaseline,
        HistoricalAverageBaseline,
        SeasonalNaiveBaseline,
    )

    results = {}
    for name, model in [
        ("persistence", PersistenceBaseline(horizon=horizon)),
        ("historical_average", HistoricalAverageBaseline(horizon=horizon)),
        ("seasonal_naive", SeasonalNaiveBaseline(season_length=5, horizon=horizon)),
    ]:
        model.fit(None, y_train)
        # X_test is only used for length; baselines ignore features
        dummy_X = X_test if X_test is not None else np.zeros((len(y_test), 1))
        y_pred = model.predict(dummy_X)
        results[name] = evaluate_regression(y_test, y_pred, prefix="")
        logger.info("Baseline %-20s  RMSE=%.6f  DirAcc=%.3f", name, results[name]["rmse"], results[name]["directional_accuracy"])
    return results