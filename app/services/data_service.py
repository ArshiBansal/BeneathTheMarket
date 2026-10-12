"""
Market-data and metadata access for the Streamlit app.

Responsibilities
----------------
- Read OHLCV and company metadata from local MongoDB
- Optionally trigger a light recent refresh via yfinance
- Expose coverage / freshness info for the status banner
- Never depend on Jupyter notebook state
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from config import settings, TICKERS, CATEGORIES
from config.tickers import get_primary_category, get_all_categories
from src.db.connection import get_db
from src.db.market_data import get_market_data, get_latest_timestamp
from src.db.company_metadata import get_company_metadata, get_all_company_metadata
from src.db.refresh_status import get_refresh_status
from src.db.analysis_results import get_analysis_results
from src.data_pipeline.yfinance_client import fetch_ohlcv
from src.data_pipeline.normalizer import normalize_ohlcv
from src.data_pipeline.validators import validate_records
from src.db.market_data import upsert_market_data
from src.db.refresh_status import update_refresh_status

logger = logging.getLogger(__name__)


class DataService:
    """Stateless helpers used by Streamlit pages."""

    # ------------------------------------------------------------------
    # Universe / metadata
    # ------------------------------------------------------------------
    @staticmethod
    def list_tickers(category: Optional[str] = None) -> List[str]:
        if category:
            return CATEGORIES.get(category, []).copy()
        return list(TICKERS)

    @staticmethod
    def list_categories() -> List[str]:
        return get_all_categories()

    @staticmethod
    def get_category(ticker: str) -> Optional[str]:
        return get_primary_category(ticker)

    @staticmethod
    def get_metadata(ticker: str) -> Dict[str, Any]:
        doc = get_company_metadata(ticker) or {}
        doc.setdefault("ticker", ticker.upper())
        doc.setdefault("primary_category", get_primary_category(ticker))
        return doc

    @staticmethod
    def get_all_metadata(category: Optional[str] = None) -> List[Dict[str, Any]]:
        return get_all_company_metadata(category=category)

    # ------------------------------------------------------------------
    # OHLCV
    # ------------------------------------------------------------------
    @staticmethod
    def load_ohlcv(
        ticker: str,
        *,
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Return a tidy OHLCV DataFrame indexed by timestamp."""
        rows = get_market_data(
            ticker, interval=interval, start=start, end=end, limit=limit
        )
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()
        cols = [
            c for c in ["open", "high", "low", "close", "volume", "adj_close"]
            if c in df.columns
        ]
        return df[cols].astype(float)

    @staticmethod
    def load_close_panel(
        tickers: List[str],
        *,
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Wide panel of close prices (columns = tickers)."""
        series = {}
        for t in tickers:
            df = DataService.load_ohlcv(t, interval=interval, start=start, end=end)
            if not df.empty and "close" in df.columns:
                series[t] = df["close"]
        if not series:
            return pd.DataFrame()
        return pd.DataFrame(series).sort_index()

    # ------------------------------------------------------------------
    # Freshness / status
    # ------------------------------------------------------------------
    @staticmethod
    def get_freshness(ticker: Optional[str] = None, interval: str = "1d") -> List[Dict[str, Any]]:
        """Return refresh_status documents for the status banner."""
        return get_refresh_status(ticker=ticker, interval=interval)

    @staticmethod
    def last_data_timestamp(ticker: str, interval: str = "1d") -> Optional[datetime]:
        return get_latest_timestamp(ticker, interval=interval)

    @staticmethod
    def coverage_summary(tickers: Optional[List[str]] = None, interval: str = "1d") -> Dict[str, Any]:
        tickers = tickers or list(TICKERS)
        present, missing = [], []
        for t in tickers:
            ts = get_latest_timestamp(t, interval)
            if ts is None:
                missing.append(t)
            else:
                present.append({"ticker": t, "last_ts": ts.isoformat()})
        return {
            "interval": interval,
            "n_requested": len(tickers),
            "n_present": len(present),
            "n_missing": len(missing),
            "missing": missing,
            "present": present,
        }

    # ------------------------------------------------------------------
    # Light on-demand refresh (optional, never blocks the UI for long)
    # ------------------------------------------------------------------
    @staticmethod
    def refresh_ticker_recent(
        ticker: str,
        *,
        interval: str = "1d",
        lookback_days: int = 5,
    ) -> int:
        """
        Fetch a short recent window from yfinance and upsert.
        Returns number of records written.  Failures are logged, not raised.
        """
        ticker = ticker.upper()
        try:
            end = datetime.utcnow()
            start = end - timedelta(days=lookback_days)
            df = fetch_ohlcv(ticker, start=start, end=end, interval=interval)
            if df is None or df.empty:
                update_refresh_status(
                    ticker, interval, success=False, error_message="Empty DataFrame"
                )
                return 0
            records = normalize_ohlcv(df, ticker, interval)
            records = validate_records(records)
            if not records:
                update_refresh_status(
                    ticker, interval, success=False, error_message="No valid records"
                )
                return 0
            result = upsert_market_data(records)
            written = result.upserted_count + result.modified_count
            update_refresh_status(
                ticker,
                interval,
                success=True,
                last_timestamp=records[-1]["timestamp"],
                records_written=written,
            )
            return written
        except Exception as exc:
            logger.warning("refresh_ticker_recent failed for %s: %s", ticker, exc)
            update_refresh_status(
                ticker, interval, success=False, error_message=str(exc)
            )
            return 0

    # ------------------------------------------------------------------
    # Analysis results (read-only)
    # ------------------------------------------------------------------
    @staticmethod
    def get_latest_analysis(
        analysis_type: str,
        ticker: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        return get_analysis_results(
            ticker=ticker, analysis_type=analysis_type, limit=limit
        )