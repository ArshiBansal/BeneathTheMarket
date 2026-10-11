# src/db/analysis_results.py
"""
CRUD helpers for analysis_results collection.
Every document is recursively sanitised so that all keys are strings.
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
    return get_db()[COLLECTIONS["analysis_results"]]


def _stringify_keys(obj: Any) -> Any:
    """Recursively turn every dict key into a str."""
    if isinstance(obj, dict):
        return {str(k): _stringify_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_keys(i) for i in obj]
    # Convert numpy / pandas scalars to plain Python types
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    return obj


def save_analysis_result(doc: Dict[str, Any]) -> str:
    """
    Store one analysis result document.
    All keys are forced to strings before insertion.
    """
    clean = _stringify_keys(doc)
    clean["ticker"] = (str(clean.get("ticker") or "")).upper() or None
    clean["created_at"] = datetime.utcnow()

    result = _coll().insert_one(clean)
    logger.debug(
        "Saved analysis_result type=%s ticker=%s id=%s",
        clean.get("analysis_type"),
        clean.get("ticker"),
        result.inserted_id,
    )
    return str(result.inserted_id)


def get_analysis_results(
    ticker: Optional[str] = None,
    analysis_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if ticker:
        query["ticker"] = ticker.upper()
    if analysis_type:
        query["analysis_type"] = analysis_type
    return list(_coll().find(query).sort("as_of", -1).limit(limit))


def delete_analysis_results(
    ticker: Optional[str] = None,
    analysis_type: Optional[str] = None,
) -> int:
    query: Dict[str, Any] = {}
    if ticker:
        query["ticker"] = ticker.upper()
    if analysis_type:
        query["analysis_type"] = analysis_type
    return _coll().delete_many(query).deleted_count