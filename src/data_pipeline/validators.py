"""
Data-quality checks and coverage reporting.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.db.market_data import get_market_data
from src.db.refresh_status import get_refresh_status
from config import TICKERS

logger = logging.getLogger(__name__)


def validate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter / annotate records that fail basic integrity checks.

    Keeps the original list shape; only rows that are completely unusable
    are dropped.  Soft problems are recorded in validation_status.
    """
    if not records:
        return []

    clean: List[Dict[str, Any]] = []
    for rec in records:
        # Must have a usable timestamp
        ts = rec.get("timestamp")
        if ts is None or (isinstance(ts, float) and pd.isna(ts)):
            continue

        # OHLC must be present and numeric
        ohlc = [rec.get(k) for k in ("open", "high", "low", "close")]
        if any(v is None for v in ohlc):
            rec["validation_status"] = "missing_ohlc"
        elif rec["high"] < rec["low"]:
            rec["validation_status"] = "high_lt_low"
        elif any(v < 0 for v in ohlc if v is not None):
            rec["validation_status"] = "negative_price"
        else:
            rec.setdefault("validation_status", "ok")

        # Volume can be zero (illiquid days) but not negative
        vol = rec.get("volume")
        if vol is not None and vol < 0:
            rec["validation_status"] = "negative_volume"

        clean.append(rec)

    dropped = len(records) - len(clean)
    if dropped:
        logger.warning("Dropped %d invalid records during validation", dropped)
    return clean


def coverage_report(
    tickers: List[str] | None = None,
    interval: str = "1d",
) -> Dict[str, Any]:
    """
    Produce a simple coverage summary for the stored market data.

    Returns a dict with:
        - total_tickers
        - tickers_with_data
        - missing_tickers
        - per_ticker: {ticker: {count, first_ts, last_ts, gaps_estimate}}
        - refresh_status_summary
    """
    tickers = tickers or TICKERS
    per_ticker = {}
    missing = []

    for ticker in tickers:
        rows = get_market_data(ticker, interval=interval)
        if not rows:
            missing.append(ticker)
            continue

        timestamps = [r["timestamp"] for r in rows]
        first_ts = min(timestamps)
        last_ts = max(timestamps)

        # Rough gap estimate (trading days ≈ 252 / year)
        span_days = (last_ts - first_ts).days or 1
        expected_approx = max(1, int(span_days * 252 / 365))
        gaps_estimate = max(0, expected_approx - len(rows))

        per_ticker[ticker] = {
            "count": len(rows),
            "first_ts": first_ts.isoformat(),
            "last_ts": last_ts.isoformat(),
            "gaps_estimate": gaps_estimate,
        }

    # Refresh status overview
    status_docs = get_refresh_status(interval=interval)
    success_count = sum(1 for d in status_docs if d.get("success"))
    fail_count = len(status_docs) - success_count

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "interval": interval,
        "total_tickers": len(tickers),
        "tickers_with_data": len(per_ticker),
        "missing_tickers": missing,
        "per_ticker": per_ticker,
        "refresh_status_summary": {
            "tracked": len(status_docs),
            "success": success_count,
            "failed": fail_count,
        },
    }
    logger.info(
        "Coverage report: %d/%d tickers have data (%s)",
        len(per_ticker),
        len(tickers),
        interval,
    )
    return report