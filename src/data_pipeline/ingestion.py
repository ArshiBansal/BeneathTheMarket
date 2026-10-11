"""
High-level ingestion orchestration.

- ingest_ticker: fetch → normalize → validate → upsert for one ticker
- backfill_universe: initial historical load for the whole candidate set
- daily_update: idempotent daily refresh of the persisted 1d bars
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from config import settings, TICKERS
from src.db.market_data import upsert_market_data, get_latest_timestamp
from src.db.company_metadata import upsert_company_metadata
from src.db.refresh_status import update_refresh_status
from src.data_pipeline.yfinance_client import fetch_ohlcv, fetch_ticker_info
from src.data_pipeline.normalizer import normalize_ohlcv
from src.data_pipeline.validators import validate_records

logger = logging.getLogger(__name__)


def ingest_ticker(
    ticker: str,
    *,
    period: Optional[str] = None,
    start: Optional[str | datetime] = None,
    end: Optional[str | datetime] = None,
    interval: str = "1d",
    update_metadata: bool = True,
) -> int:
    """
    Full pipeline for a single ticker.

    Returns the number of records written (0 on failure).
    """
    ticker = ticker.upper()
    logger.info("Ingesting %s (interval=%s)", ticker, interval)

    try:
        df = fetch_ohlcv(
            ticker,
            period=period,
            start=start,
            end=end,
            interval=interval,
        )
        if df.empty:
            update_refresh_status(
                ticker,
                interval,
                success=False,
                error_message="Empty DataFrame from yfinance",
            )
            return 0

        # Optional currency from ticker info
        currency = None
        if update_metadata:
            info = fetch_ticker_info(ticker)
            currency = info.get("currency")
            # Persist metadata (primary_category is added later by the caller if needed)
            upsert_company_metadata(info)

        records = normalize_ohlcv(df, ticker, interval, currency=currency)
        records = validate_records(records)

        if not records:
            update_refresh_status(
                ticker,
                interval,
                success=False,
                error_message="No valid records after normalization/validation",
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
        logger.info("Ingested %s → %d records written", ticker, written)
        return written

    except Exception as exc:
        logger.exception("Ingestion failed for %s: %s", ticker, exc)
        update_refresh_status(
            ticker,
            interval,
            success=False,
            error_message=str(exc),
        )
        return 0


def backfill_universe(
    tickers: Optional[List[str]] = None,
    *,
    period: str = "5y",
    interval: str = "1d",
) -> dict:
    """
    Initial historical load for the candidate universe.

    Returns a summary dict: {ticker: records_written}.
    """
    tickers = tickers or TICKERS
    summary = {}
    logger.info("Starting backfill for %d tickers (period=%s)", len(tickers), period)

    for i, ticker in enumerate(tickers, 1):
        logger.info("[%d/%d] Backfilling %s", i, len(tickers), ticker)
        written = ingest_ticker(
            ticker,
            period=period,
            interval=interval,
            update_metadata=True,
        )
        summary[ticker] = written

    total = sum(summary.values())
    logger.info("Backfill finished – total records written: %d", total)
    return summary


def daily_update(
    tickers: Optional[List[str]] = None,
    *,
    lookback_days: int = 5,
) -> dict:
    """
    Idempotent daily update.

    Fetches only a short recent window and relies on upsert to avoid
    duplicates.  Suitable for a scheduled job that runs once per day.
    """
    tickers = tickers or TICKERS
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)
    summary = {}

    logger.info(
        "Daily update for %d tickers (start=%s, end=%s)",
        len(tickers),
        start.date(),
        end.date(),
    )

    for ticker in tickers:
        # Skip if we already have today's bar (optional optimisation)
        latest = get_latest_timestamp(ticker, "1d")
        if latest and latest.date() >= end.date():
            logger.debug("%s already up-to-date (latest=%s)", ticker, latest.date())
            summary[ticker] = 0
            continue

        written = ingest_ticker(
            ticker,
            start=start,
            end=end,
            interval="1d",
            update_metadata=False,  # metadata rarely changes daily
        )
        summary[ticker] = written

    return summary