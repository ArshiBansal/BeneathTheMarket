# src/db/refresh_status.py
"""
CRUD helpers for refresh_status collection.
Tracks last successful retrieval, errors and coverage per ticker/interval.
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
    return get_db()[COLLECTIONS["refresh_status"]]


def update_refresh_status(
    ticker: str,
    interval: str,
    *,
    success: bool,
    last_timestamp: Optional[datetime] = None,
    error_message: Optional[str] = None,
    records_written: int = 0,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Upsert the refresh status for a ticker + interval pair.
    """
    now = datetime.utcnow()
    ticker = ticker.upper()

    update: Dict[str, Any] = {
        "ticker": ticker,
        "interval": interval,
        "last_attempt_at": now,
        "success": success,
        "records_written": records_written,
    }
    if success:
        update["last_success_at"] = now
        if last_timestamp is not None:
            update["last_data_timestamp"] = last_timestamp
        update["last_error"] = None
    else:
        update["last_error"] = error_message or "Unknown error"

    if extra:
        update.update(extra)

    _coll().update_one(
        {"ticker": ticker, "interval": interval},
        {"$set": update},
        upsert=True,
    )
    logger.debug(
        "Refresh status updated: %s/%s success=%s",
        ticker,
        interval,
        success,
    )


def get_refresh_status(
    ticker: Optional[str] = None,
    interval: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return refresh status documents, optionally filtered."""
    query: Dict[str, Any] = {}
    if ticker:
        query["ticker"] = ticker.upper()
    if interval:
        query["interval"] = interval
    return list(_coll().find(query).sort("ticker", 1))


def get_stale_tickers(
    interval: str = "1d",
    older_than_hours: int = 25,
) -> List[str]:
    """
    Return tickers whose last successful daily refresh is older than
    the given threshold (useful for daily update jobs).
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
    cursor = _coll().find(
        {
            "interval": interval,
            "$or": [
                {"last_success_at": {"$lt": cutoff}},
                {"last_success_at": {"$exists": False}},
                {"success": False},
            ],
        },
        {"ticker": 1},
    )
    return [doc["ticker"] for doc in cursor]