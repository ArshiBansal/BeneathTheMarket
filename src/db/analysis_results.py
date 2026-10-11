# src/db/analysis_results.py
"""
CRUD helpers for analysis_results collection.
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


def save_analysis_result(doc: Dict[str, Any]) -> str:
    """
    Store one analysis result document.

    Expected keys (flexible):
        ticker, analysis_type, as_of, payload, config, created_at
    Returns the inserted _id as string.
    """
    doc = {
        **doc,
        "ticker": doc.get("ticker", "").upper() if doc.get("ticker") else None,
        "created_at": datetime.utcnow(),
    }
    result = _coll().insert_one(doc)
    logger.debug(
        "Saved analysis_result type=%s ticker=%s id=%s",
        doc.get("analysis_type"),
        doc.get("ticker"),
        result.inserted_id,
    )
    return str(result.inserted_id)


def get_analysis_results(
    ticker: Optional[str] = None,
    analysis_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query analysis results with optional filters."""
    query: Dict[str, Any] = {}
    if ticker:
        query["ticker"] = ticker.upper()
    if analysis_type:
        query["analysis_type"] = analysis_type

    cursor = (
        _coll()
        .find(query)
        .sort("as_of", -1)
        .limit(limit)
    )
    return list(cursor)


def delete_analysis_results(
    ticker: Optional[str] = None,
    analysis_type: Optional[str] = None,
) -> int:
    """Delete matching analysis results. Returns deleted count."""
    query: Dict[str, Any] = {}
    if ticker:
        query["ticker"] = ticker.upper()
    if analysis_type:
        query["analysis_type"] = analysis_type
    result = _coll().delete_many(query)
    return result.deleted_count