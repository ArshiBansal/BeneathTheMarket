"""
Normalize raw yfinance DataFrames into clean dictionaries ready for MongoDB.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_ohlcv(
    df: pd.DataFrame,
    ticker: str,
    interval: str,
    *,
    source: str = "yfinance",
    currency: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Convert a yfinance OHLCV DataFrame into a list of MongoDB-ready documents.

    Each document contains:
        ticker, interval, timestamp, open, high, low, close, volume,
        adj_close (if present), currency, source, retrieved_at, validation_status
    """
    if df is None or df.empty:
        return []

    ticker = ticker.upper()
    now = datetime.utcnow()
    records: List[Dict[str, Any]] = []

    # Standardise column names (yfinance can return slightly different casings)
    col_map = {c.lower(): c for c in df.columns}
    required = ["open", "high", "low", "close", "volume"]
    for col in required:
        if col not in col_map:
            logger.error("Missing required column '%s' for %s", col, ticker)
            return []

    for ts, row in df.iterrows():
        # Guard against NaT or non-datetime index
        if not isinstance(ts, (pd.Timestamp, datetime)):
            continue

        timestamp = ts.to_pydatetime() if isinstance(ts, pd.Timestamp) else ts

        rec: Dict[str, Any] = {
            "ticker": ticker,
            "interval": interval,
            "timestamp": timestamp,
            "open": _safe_float(row[col_map["open"]]),
            "high": _safe_float(row[col_map["high"]]),
            "low": _safe_float(row[col_map["low"]]),
            "close": _safe_float(row[col_map["close"]]),
            "volume": _safe_float(row[col_map["volume"]]),
            "source": source,
            "retrieved_at": now,
            "validation_status": "ok",
        }

        if "adj close" in col_map:
            rec["adj_close"] = _safe_float(row[col_map["adj close"]])
        if currency:
            rec["currency"] = currency

        # Basic sanity check – mark bad rows
        if any(v is None for v in (rec["open"], rec["high"], rec["low"], rec["close"])):
            rec["validation_status"] = "missing_ohlc"
        elif rec["high"] < rec["low"]:
            rec["validation_status"] = "high_lt_low"

        records.append(rec)

    logger.debug("Normalized %d records for %s (%s)", len(records), ticker, interval)
    return records


def _safe_float(value: Any) -> float | None:
    """Convert to float or return None for NaN / None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None