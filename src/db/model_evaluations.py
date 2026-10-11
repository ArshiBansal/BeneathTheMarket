# src/db/model_evaluations.py
"""
CRUD helpers for model_evaluations collection.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo.collection import Collection

from .connection import get_db
from .collections import COLLECTIONS

logger = logging.getLogger(__name__)


def _coll() -> Collection:
    return get_db()[COLLECTIONS["model_evaluations"]]


def save_model_evaluation(doc: Dict[str, Any]) -> str:
    """
    Store one model evaluation record.

    Typical keys:
        model_id, model_type, target, metrics, evaluation_period,
        train_end, test_start, test_end, config, created_at
    """
    doc = {
        **doc,
        "evaluation_date": doc.get("evaluation_date", datetime.utcnow()),
        "created_at": datetime.utcnow(),
    }
    result = _coll().insert_one(doc)
    logger.debug(
        "Saved model_evaluation model_id=%s metrics=%s",
        doc.get("model_id"),
        list(doc.get("metrics", {}).keys()),
    )
    return str(result.inserted_id)


def get_model_evaluations(
    model_id: Optional[str] = None,
    model_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query evaluation records, newest first."""
    query: Dict[str, Any] = {}
    if model_id:
        query["model_id"] = model_id
    if model_type:
        query["model_type"] = model_type

    cursor = (
        _coll()
        .find(query)
        .sort("evaluation_date", -1)
        .limit(limit)
    )
    return list(cursor)


def get_best_evaluation(
    metric: str = "rmse",
    model_type: Optional[str] = None,
    higher_is_better: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Return the evaluation document that has the best value for the given metric.
    """
    query: Dict[str, Any] = {f"metrics.{metric}": {"$exists": True}}
    if model_type:
        query["model_type"] = model_type

    sort_order = -1 if higher_is_better else 1
    return _coll().find_one(
        query,
        sort=[(f"metrics.{metric}", sort_order)],
    )