"""
Idempotent daily update of persisted 1d bars.

Fetches a short recent window and upserts into market_data.
Suitable for a scheduled task (cron / Task Scheduler) once per day.

Usage
-----
    python scripts/daily_update.py
    python scripts/daily_update.py --lookback-days 7 --from-validated
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
from src.data_pipeline.ingestion import daily_update

setup_logging(level="INFO")
logger = get_logger(__name__)


def _load_validated_tickers() -> list[str]:
    path = settings.PROCESSED_DATA_DIR / "validated_tickers.csv"
    if not path.exists():
        return list(TICKERS)
    df = pd.read_csv(path)
    return df["ticker"].str.upper().tolist()


def main(lookback_days: int = 5, from_validated: bool = True) -> None:
    get_client()
    ensure_indexes()

    tickers = _load_validated_tickers() if from_validated else list(TICKERS)
    logger.info(
        "Daily update – %d tickers, lookback_days=%d",
        len(tickers),
        lookback_days,
    )
    summary = daily_update(tickers=tickers, lookback_days=lookback_days)
    total = sum(summary.values())
    logger.info("Daily update finished – total records written: %d", total)
    close_client()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily market-data update")
    parser.add_argument("--lookback-days", type=int, default=5)
    parser.add_argument(
        "--from-validated",
        action="store_true",
        default=True,
        help="Use validated ticker list (default: True)",
    )
    parser.add_argument(
        "--all-tickers",
        action="store_true",
        help="Use full candidate universe instead of validated list",
    )
    args = parser.parse_args()
    main(
        lookback_days=args.lookback_days,
        from_validated=not args.all_tickers,
    )