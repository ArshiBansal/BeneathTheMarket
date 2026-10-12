"""
Tests for chronological splits and metric helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.evaluation import (
    chronological_split,
    walk_forward_split,
    evaluate_regression,
    evaluate_classification,
    evaluate_clustering,
)
from src.models.baselines import (
    PersistenceBaseline,
    HistoricalAverageBaseline,
    SeasonalNaiveBaseline,
)


def test_chronological_split_order():
    split = chronological_split(1000, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    assert split.train_idx.max() < split.val_idx.min() or len(split.val_idx) == 0
    if len(split.val_idx) and len(split.test_idx):
        assert split.val_idx.max() < split.test_idx.min()
    assert len(split.train_idx) + len(split.val_idx) + len(split.test_idx) <= 1000


def test_chronological_split_ratios():
    with pytest.raises(ValueError):
        chronological_split(100, train_ratio=0.5, val_ratio=0.5, test_ratio=0.5)


def test_walk_forward_split():
    splits = walk_forward_split(500, n_splits=3, train_min_size=100, test_size=50)
    assert len(splits) >= 1
    for s in splits:
        if len(s.test_idx):
            assert s.train_idx.max() < s.test_idx.min()


def test_evaluate_regression():
    y_true = np.array([0.01, -0.02, 0.03, 0.0, -0.01])
    y_pred = np.array([0.005, -0.01, 0.02, 0.01, -0.005])
    m = evaluate_regression(y_true, y_pred)
    assert "mae" in m and "rmse" in m and "r2" in m
    assert m["mae"] >= 0
    assert m["rmse"] >= 0


def test_evaluate_classification():
    y_true = np.array([1, 0, 1, 1, 0, 0, 1])
    y_pred = np.array([1, 0, 0, 1, 0, 1, 1])
    m = evaluate_classification(y_true, y_pred)
    assert "accuracy" in m
    assert 0 <= m["accuracy"] <= 1
    assert "confusion_matrix" in m


def test_evaluate_clustering():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(50, 3))
    labels = np.array([0] * 25 + [1] * 25)
    m = evaluate_clustering(X, labels)
    assert "silhouette" in m
    assert m["n_clusters"] == 2


def test_persistence_baseline():
    y = np.array([0.01, 0.02, -0.01, 0.0])
    model = PersistenceBaseline()
    model.fit(None, y)
    pred = model.predict(np.zeros((3, 1)))
    assert np.allclose(pred, y[-1])


def test_historical_average_baseline():
    y = np.array([0.01, 0.02, -0.01, 0.0])
    model = HistoricalAverageBaseline()
    model.fit(None, y)
    pred = model.predict(np.zeros((2, 1)))
    assert np.allclose(pred, y.mean())


def test_seasonal_naive_baseline():
    y = np.arange(10, dtype=float)
    model = SeasonalNaiveBaseline(season_length=5)
    model.fit(None, y)
    pred = model.predict(np.zeros((3, 1)))
    assert len(pred) == 3