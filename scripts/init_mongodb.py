"""
Initialise the local MongoDB database for the project.

- Creates the database (implicitly on first write)
- Ensures all required indexes
- Optionally seeds company_metadata for the candidate universe

Usage
-----
    python scripts/init_mongodb.py
    python scripts/init_mongodb.py --seed-metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, TICKERS, CATEGORIES
from config.tickers import get_primary_category
from src.utils import setup_logging, get_logger
from src.db.connection import get_client, get_db, close_client
from src.db.collections import ensure_indexes, COLLECTIONS
from src.db.company_metadata import upsert_company_metadata
from src.data_pipeline.yfinance_client import fetch_ticker_info

setup_logging(level="INFO")
logger = get_logger(__name__)


def main(seed_metadata: bool = False) -> None:
    logger.info("Connecting to local MongoDB at %s", settings.MONGODB_URI)
    client = get_client()
    db = get_db()
    logger.info("Database: %s", settings.MONGODB_DB_NAME)

    logger.info("Ensuring indexes...")
    ensure_indexes(db)
    logger.info("Indexes ready. Collections: %s", db.list_collection_names())

    if seed_metadata:
        logger.info("Seeding company_metadata for %d tickers...", len(TICKERS))
        ok, fail = 0, 0
        for i, ticker in enumerate(TICKERS, 1):
            try:
                info = fetch_ticker_info(ticker)
                info["primary_category"] = get_primary_category(ticker)
                upsert_company_metadata(info)
                ok += 1
                logger.info("[%d/%d] %s OK", i, len(TICKERS), ticker)
            except Exception as exc:
                fail += 1
                logger.warning("[%d/%d] %s FAILED: %s", i, len(TICKERS), ticker, exc)
        logger.info("Metadata seed finished – ok=%d fail=%d", ok, fail)

    close_client()
    logger.info("init_mongodb.py finished successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialise local MongoDB for the project")
    parser.add_argument(
        "--seed-metadata",
        action="store_true",
        help="Fetch and store company_metadata for the candidate universe",
    )
    args = parser.parse_args()
    main(seed_metadata=args.seed_metadata)