"""
Historical backfill of daily OHLCV for the validated (or full) universe.

Idempotent: uses upserts on (ticker, interval, timestamp).

Usage
-----
    python scripts/backfill_market_data.py
    python scripts/backfill_market_data.py --period 5y --tickers AAPL MSFT
    python scripts/backfill_market_data.py --from-validated
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, TICKERS
from src.utils import setup_logging, get_logger
from src.db.connection import get_client, close_client
from src.db.collections import ensure_indexes
from src.data_pipeline.ingestion import backfill_universe

setup_logging(level="INFO")
logger = get_logger(__name__)


def _load_validated_tickers() -> list[str]:
    path = settings.PROCESSED_DATA_DIR / "validated_tickers.csv"
    if not path.exists():
        logger.warning("validated_tickers.csv not found – using full TICKERS list")
        return list(TICKERS)
    df = pd.read_csv(path)
    return df["ticker"].str.upper().tolist()


def main(
    period: str = "5y",
    interval: str = "1d",
    tickers: list[str] | None = None,
    from_validated: bool = False,
) -> None:
    get_client()
    ensure_indexes()

    if tickers:
        universe = [t.upper() for t in tickers]
    elif from_validated:
        universe = _load_validated_tickers()
    else:
        universe = list(TICKERS)

    logger.info(
        "Backfill starting – %d tickers, period=%s, interval=%s",
        len(universe),
        period,
        interval,
    )
    summary = backfill_universe(tickers=universe, period=period, interval=interval)
    total = sum(summary.values())
    logger.info("Backfill finished – total records written: %d", total)
    for t, n in sorted(summary.items(), key=lambda x: -x[1])[:10]:
        logger.info("  %s: %d", t, n)

    close_client()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill historical market data")
    parser.add_argument("--period", default="5y", help="yfinance period string")
    parser.add_argument("--interval", default="1d", help="Bar interval")
    parser.add_argument("--tickers", nargs="*", help="Specific tickers (default: all)")
    parser.add_argument(
        "--from-validated",
        action="store_true",
        help="Use data/processed/validated_tickers.csv",
    )
    args = parser.parse_args()
    main(
        period=args.period,
        interval=args.interval,
        tickers=args.tickers,
        from_validated=args.from_validated,
    )