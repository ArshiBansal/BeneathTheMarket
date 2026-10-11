"""
Hourly (or on-demand) refresh of recent bars.

Separates the “current view” from the daily persisted history.
Only intervals that yfinance actually supports for the given ticker
will succeed; failures are logged in refresh_status.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from config import settings, TICKERS
from src.db.market_data import upsert_market_data
from src.db.refresh_status import update_refresh_status
from src.data_pipeline.yfinance_client import fetch_ohlcv
from src.data_pipeline.normalizer import normalize_ohlcv
from src.data_pipeline.validators import validate_records

logger = logging.getLogger(__name__)


def refresh_recent(
    ticker: str,
    *,
    interval: str = "1h",
    lookback_hours: int = 48,
) -> int:
    """
    Fetch the most recent bars for a single ticker and upsert them.

    Returns number of records written.
    """
    if not settings.HOURLY_REFRESH_ENABLED and interval.endswith("h"):
        logger.debug("Hourly refresh disabled by settings – skipping %s", ticker)
        return 0

    ticker = ticker.upper()
    end = datetime.utcnow()
    start = end - timedelta(hours=lookback_hours)

    logger.debug("Refreshing recent data for %s (%s)", ticker, interval)

    try:
        df = fetch_ohlcv(
            ticker,
            start=start,
            end=end,
            interval=interval,
        )
        if df.empty:
            update_refresh_status(
                ticker,
                interval,
                success=False,
                error_message="Empty recent DataFrame",
            )
            return 0

        records = normalize_ohlcv(df, ticker, interval)
        records = validate_records(records)
        if not records:
            update_refresh_status(
                ticker,
                interval,
                success=False,
                error_message="No valid recent records",
            )
            return 0

        result = upsert_market_data(records)
        written = result.upserted_count + result.modified_count
        last_ts = records[-1]["timestamp"]

        update_refresh_status(
            ticker,
            interval,
            success=True,
            last_timestamp=last_ts,
            records_written=written,
        )
        return written

    except Exception as exc:
        logger.warning("Recent refresh failed for %s: %s", ticker, exc)
        update_refresh_status(
            ticker,
            interval,
            success=False,
            error_message=str(exc),
        )
        return 0


def refresh_universe_recent(
    tickers: Optional[List[str]] = None,
    *,
    interval: str = "1h",
    lookback_hours: int = 48,
) -> dict:
    """
    Refresh recent bars for the whole (or a subset of the) universe.

    Returns {ticker: records_written}.
    """
    tickers = tickers or TICKERS
    summary = {}
    logger.info(
        "Refreshing recent (%s) data for %d tickers",
        interval,
        len(tickers),
    )

    for ticker in tickers:
        written = refresh_recent(
            ticker,
            interval=interval,
            lookback_hours=lookback_hours,
        )
        summary[ticker] = written

    total = sum(summary.values())
    logger.info("Recent refresh finished – total records written: %d", total)
    return summary