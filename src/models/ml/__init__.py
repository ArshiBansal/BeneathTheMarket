"""
Classical machine-learning models and trainers.

Public API
----------
from src.models.ml import (
    get_ml_model,
    MLTrainer,
    ML_MODEL_NAMES,
)
"""

from .models import get_ml_model, ML_MODEL_NAMES
from .trainers import MLTrainer

__all__ = [
    "get_ml_model",
    "MLTrainer",
    "ML_MODEL_NAMES",
]