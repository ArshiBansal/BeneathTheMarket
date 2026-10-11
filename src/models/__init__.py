"""
Machine-learning & deep-learning model package.

Sub-packages
------------
ml/          classical ML algorithms (>3 required)
dl/          deep-learning sequence models (>3 required)

Top-level modules
-----------------
baselines.py     simple persistence / historical-average baselines
evaluation.py    chronological train/val/test, metrics, walk-forward
registry.py      versioned model metadata & artifact paths

Public API
----------
from src.models import (
    PersistenceBaseline,
    HistoricalAverageBaseline,
    chronological_split,
    evaluate_regression,
    evaluate_classification,
    ModelRegistry,
)
"""

from .baselines import PersistenceBaseline, HistoricalAverageBaseline
from .evaluation import (
    chronological_split,
    walk_forward_split,
    evaluate_regression,
    evaluate_classification,
    evaluate_clustering,
)
from .registry import ModelRegistry

__all__ = [
    "PersistenceBaseline",
    "HistoricalAverageBaseline",
    "chronological_split",
    "walk_forward_split",
    "evaluate_regression",
    "evaluate_classification",
    "evaluate_clustering",
    "ModelRegistry",
]