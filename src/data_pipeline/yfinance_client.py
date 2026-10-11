"""
Thin, robust wrapper around the yfinance library.

Responsible only for talking to the upstream source and returning
raw pandas DataFrames / dicts.  No MongoDB logic lives here.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf

from config import settings

logger = logging.getLogger(__name__)


def fetch_ohlcv(
    ticker: str,
    *,
    period: Optional[str] = None,
    start: Optional[str | datetime] = None,
    end: Optional[str | datetime] = None,
    interval: str = "1d",
    auto_adjust: bool = True,
    timeout: Optional[int] = None,
) -> pd.DataFrame:
    """
    Download OHLCV data for a single ticker.

    Parameters
    ----------
    ticker : str
        Yahoo Finance ticker symbol.
    period : str, optional
        Valid yfinance period string (e.g. "5y", "1y", "6mo").
        Ignored when start/end are supplied.
    start, end : str or datetime, optional
        Explicit date range.
    interval : str
        Bar size ("1d", "1h", "1wk", …).
    auto_adjust : bool
        Whether to auto-adjust OHLC for splits/dividends.
    timeout : int, optional
        Override default request timeout.

    Returns
    -------
    pd.DataFrame
        Columns: Open, High, Low, Close, Volume (and Adj Close if present).
        Index is a DatetimeIndex (UTC-naive, normalized).
        Empty DataFrame on failure.
    """
    ticker = ticker.upper().strip()
    timeout = timeout or settings.REQUEST_TIMEOUT
    period = period or settings.DEFAULT_HISTORY_PERIOD

    for attempt in range(1, settings.MAX_RETRIES + 1):
        try:
            t = yf.Ticker(ticker)
            kwargs: Dict[str, Any] = {
                "interval": interval,
                "auto_adjust": auto_adjust,
                "timeout": timeout,
            }
            if start is not None or end is not None:
                kwargs["start"] = start
                kwargs["end"] = end
            else:
                kwargs["period"] = period

            df = t.history(**kwargs)

            if df is None or df.empty:
                logger.warning(
                    "yfinance returned empty data for %s (interval=%s, attempt=%d)",
                    ticker,
                    interval,
                    attempt,
                )
                return pd.DataFrame()

            # Ensure timezone-naive index for consistent storage
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)
            df.index = df.index.normalize() if interval in ("1d", "1wk", "1mo") else df.index

            logger.debug(
                "Fetched %d rows for %s (%s) attempt=%d",
                len(df),
                ticker,
                interval,
                attempt,
            )
            return df

        except Exception as exc:
            logger.warning(
                "yfinance fetch failed for %s (attempt %d/%d): %s",
                ticker,
                attempt,
                settings.MAX_RETRIES,
                exc,
            )
            if attempt < settings.MAX_RETRIES:
                time.sleep(1.5 * attempt)
            else:
                logger.error("All retries exhausted for %s", ticker)
                return pd.DataFrame()


def fetch_ticker_info(ticker: str) -> Dict[str, Any]:
    """
    Retrieve static metadata for a ticker (name, sector, industry, …).

    Returns an empty dict on failure so callers never receive None.
    """
    ticker = ticker.upper().strip()
    try:
        info = yf.Ticker(ticker).info or {}
        # Keep only the most useful, stable fields
        return {
            "ticker": ticker,
            "short_name": info.get("shortName") or info.get("longName"),
            "long_name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
            "quote_type": info.get("quoteType"),
            "website": info.get("website"),
            "retrieved_at": datetime.utcnow(),
        }
    except Exception as exc:
        logger.warning("Could not fetch info for %s: %s", ticker, exc)
        return {"ticker": ticker, "retrieved_at": datetime.utcnow()}