"""
CRUD helpers for company_metadata collection.
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
    return get_db()[COLLECTIONS["company_metadata"]]


def upsert_company_metadata(doc: Dict[str, Any]) -> None:
    """
    Insert or update a single company metadata document.
    Required key: ticker
    """
    ticker = doc["ticker"].upper()
    doc = {**doc, "ticker": ticker, "updated_at": datetime.utcnow()}
    _coll().update_one(
        {"ticker": ticker},
        {"$set": doc},
        upsert=True,
    )
    logger.debug("Upserted company_metadata for %s", ticker)


def get_company_metadata(ticker: str) -> Optional[Dict[str, Any]]:
    """Return metadata for one ticker or None."""
    return _coll().find_one({"ticker": ticker.upper()})


def get_all_company_metadata(
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return all metadata documents, optionally filtered by primary category."""
    query: Dict[str, Any] = {}
    if category:
        query["primary_category"] = category
    return list(_coll().find(query).sort("ticker", 1))


def bulk_upsert_company_metadata(docs: List[Dict[str, Any]]) -> int:
    """Upsert many metadata documents. Returns number of upserted/updated docs."""
    count = 0
    for doc in docs:
        upsert_company_metadata(doc)
        count += 1
    return count