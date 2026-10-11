# src/db/predictions.py
"""
CRUD helpers for the predictions collection.
Each forecast is stored as a dated record (never overwritten).
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
    return get_db()[COLLECTIONS["predictions"]]


def save_prediction(doc: Dict[str, Any]) -> str:
    """
    Persist one forecast record.

    Required / recommended keys:
        ticker, horizon, predicted_value (or predicted_return),
        model_id, model_version, input_cutoff, generated_at
    """
    now = datetime.utcnow()
    doc = {
        **doc,
        "ticker": doc["ticker"].upper(),
        "generated_at": doc.get("generated_at", now),
        "created_at": now,
    }
    result = _coll().insert_one(doc)
    logger.debug(
        "Saved prediction ticker=%s horizon=%s model=%s",
        doc["ticker"],
        doc.get("horizon"),
        doc.get("model_id"),
    )
    return str(result.inserted_id)


def get_predictions(
    ticker: Optional[str] = None,
    horizon: Optional[int] = None,
    model_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return prediction history, newest first."""
    query: Dict[str, Any] = {}
    if ticker:
        query["ticker"] = ticker.upper()
    if horizon is not None:
        query["horizon"] = horizon
    if model_id:
        query["model_id"] = model_id

    cursor = (
        _coll()
        .find(query)
        .sort("generated_at", -1)
        .limit(limit)
    )
    return list(cursor)


def get_latest_prediction(
    ticker: str,
    horizon: int,
    model_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent forecast for the given ticker/horizon."""
    query: Dict[str, Any] = {
        "ticker": ticker.upper(),
        "horizon": horizon,
    }
    if model_id:
        query["model_id"] = model_id

    return _coll().find_one(query, sort=[("generated_at", -1)])