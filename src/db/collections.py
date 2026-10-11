# src/db/collections.py
"""
Collection name constants and index creation.
"""

from __future__ import annotations

import logging
from typing import Dict

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from config.constants import COLLECTIONS as _COLLECTIONS
from .connection import get_db

logger = logging.getLogger(__name__)

# Re-export for convenience
COLLECTIONS: Dict[str, str] = _COLLECTIONS


def ensure_indexes(db: Database | None = None) -> None:
    """
    Create all required indexes.  Safe to call multiple times (idempotent).
    """
    if db is None:
        db = get_db()

    # market_data – unique key prevents duplicate bars
    db[COLLECTIONS["market_data"]].create_index(
        [("ticker", ASCENDING), ("interval", ASCENDING), ("timestamp", ASCENDING)],
        unique=True,
        name="uniq_ticker_interval_ts",
    )
    db[COLLECTIONS["market_data"]].create_index(
        [("ticker", ASCENDING), ("timestamp", DESCENDING)],
        name="ticker_ts_desc",
    )

    # company_metadata
    db[COLLECTIONS["company_metadata"]].create_index(
        [("ticker", ASCENDING)],
        unique=True,
        name="uniq_ticker",
    )

    # analysis_results
    db[COLLECTIONS["analysis_results"]].create_index(
        [("ticker", ASCENDING), ("analysis_type", ASCENDING), ("as_of", DESCENDING)],
        name="ticker_type_asof",
    )

    # predictions – keep history of every forecast
    db[COLLECTIONS["predictions"]].create_index(
        [("ticker", ASCENDING), ("horizon", ASCENDING), ("generated_at", DESCENDING)],
        name="ticker_horizon_generated",
    )
    db[COLLECTIONS["predictions"]].create_index(
        [("model_id", ASCENDING), ("generated_at", DESCENDING)],
        name="model_generated",
    )

    # model_evaluations
    db[COLLECTIONS["model_evaluations"]].create_index(
        [("model_id", ASCENDING), ("evaluation_date", DESCENDING)],
        name="model_eval_date",
    )

    # refresh_status
    db[COLLECTIONS["refresh_status"]].create_index(
        [("ticker", ASCENDING), ("interval", ASCENDING)],
        unique=True,
        name="uniq_ticker_interval",
    )

    logger.info("All MongoDB indexes ensured.")