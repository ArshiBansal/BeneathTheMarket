"""
CRUD helpers for the market_data collection.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.results import BulkWriteResult

from .connection import get_db
from .collections import COLLECTIONS

logger = logging.getLogger(__name__)


def _coll() -> Collection:
    return get_db()[COLLECTIONS["market_data"]]


def upsert_market_data(records: List[Dict[str, Any]]) -> BulkWriteResult:
    """
    Idempotent bulk upsert of OHLCV bars.

    Each record must contain at least:
        ticker, interval, timestamp, open, high, low, close, volume
    Optional: adj_close, currency, source, retrieved_at, validation_status
    """
    if not records:
        return BulkWriteResult({}, acknowledged=True)

    ops = []
    now = datetime.utcnow()
    for rec in records:
        key = {
            "ticker": rec["ticker"].upper(),
            "interval": rec["interval"],
            "timestamp": rec["timestamp"],
        }
        doc = {**rec, "ticker": key["ticker"], "updated_at": now}
        if "retrieved_at" not in doc:
            doc["retrieved_at"] = now
        ops.append(
            UpdateOne(
                key,
                {"$set": doc},
                upsert=True,
            )
        )

    result = _coll().bulk_write(ops, ordered=False)
    logger.debug(
        "Upserted market_data: matched=%s, modified=%s, upserted=%s",
        result.matched_count,
        result.modified_count,
        result.upserted_count,
    )
    return result


def get_market_data(
    ticker: str,
    interval: str = "1d",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return OHLCV documents for a ticker, sorted by timestamp ascending."""
    query: Dict[str, Any] = {
        "ticker": ticker.upper(),
        "interval": interval,
    }
    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = start
        if end:
            query["timestamp"]["$lte"] = end

    cursor = _coll().find(query).sort("timestamp", 1)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def get_latest_timestamp(ticker: str, interval: str = "1d") -> Optional[datetime]:
    """Return the most recent timestamp stored for a ticker/interval."""
    doc = (
        _coll()
        .find({"ticker": ticker.upper(), "interval": interval})
        .sort("timestamp", -1)
        .limit(1)
    )
    docs = list(doc)
    return docs[0]["timestamp"] if docs else None


def delete_market_data(ticker: str, interval: Optional[str] = None) -> int:
    """Delete all (or interval-specific) bars for a ticker. Returns deleted count."""
    query: Dict[str, Any] = {"ticker": ticker.upper()}
    if interval:
        query["interval"] = interval
    result = _coll().delete_many(query)
    return result.deleted_count