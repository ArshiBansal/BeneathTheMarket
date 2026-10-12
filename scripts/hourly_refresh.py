"""
Hourly (or on-demand) refresh of recent bars.

Only useful when HOURLY_REFRESH_ENABLED=true in settings and a process
is actually running. Does not invent live data when the upstream source
is unavailable.

Usage
-----
    python scripts/hourly_refresh.py
    python scripts/hourly_refresh.py --interval 1h --lookback-hours 48
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
from src.data_pipeline.refresh import refresh_universe_recent

setup_logging(level="INFO")
logger = get_logger(__name__)


def _load_validated_tickers() -> list[str]:
    path = settings.PROCESSED_DATA_DIR / "validated_tickers.csv"
    if not path.exists():
        return list(TICKERS)
    df = pd.read_csv(path)
    return df["ticker"].str.upper().tolist()


def main(
    interval: str = "1h",
    lookback_hours: int = 48,
    from_validated: bool = True,
) -> None:
    if not settings.HOURLY_REFRESH_ENABLED and interval.endswith("h"):
        logger.warning(
            "HOURLY_REFRESH_ENABLED is false – refresh will be skipped for hourly intervals"
        )

    get_client()
    ensure_indexes()

    tickers = _load_validated_tickers() if from_validated else list(TICKERS)
    logger.info(
        "Recent refresh – %d tickers, interval=%s, lookback_hours=%d",
        len(tickers),
        interval,
        lookback_hours,
    )
    summary = refresh_universe_recent(
        tickers=tickers,
        interval=interval,
        lookback_hours=lookback_hours,
    )
    total = sum(summary.values())
    logger.info("Recent refresh finished – total records written: %d", total)
    close_client()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hourly / recent market-data refresh")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--lookback-hours", type=int, default=48)
    parser.add_argument(
        "--all-tickers",
        action="store_true",
        help="Use full candidate universe",
    )
    args = parser.parse_args()
    main(
        interval=args.interval,
        lookback_hours=args.lookback_hours,
        from_validated=not args.all_tickers,
    )