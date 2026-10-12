"""
Tests for the local MongoDB access layer.

These tests require a running local mongod on localhost:27017.
They are skipped automatically when MongoDB is unreachable.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connection import get_client, get_db, close_client
from src.db.collections import ensure_indexes, COLLECTIONS
from src.db.market_data import (
    upsert_market_data,
    get_market_data,
    get_latest_timestamp,
    delete_market_data,
)
from src.db.company_metadata import upsert_company_metadata, get_company_metadata
from src.db.predictions import save_prediction, get_predictions
from src.db.refresh_status import update_refresh_status, get_refresh_status


def _mongo_available() -> bool:
    try:
        client = get_client()
        client.admin.command("ping")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _mongo_available(),
    reason="Local MongoDB is not reachable",
)


@pytest.fixture(scope="module", autouse=True)
def _setup_db():
    get_client()
    ensure_indexes()
    yield
    close_client()


def test_ensure_indexes():
    db = get_db()
    ensure_indexes(db)
    names = db.list_collection_names()
    assert isinstance(names, list)


def test_market_data_upsert_and_read():
    ticker = "_TEST_AAPL"
    ts = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    records = [
        {
            "ticker": ticker,
            "interval": "1d",
            "timestamp": ts,
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 1_000_000,
            "source": "test",
            "validation_status": "ok",
        }
    ]
    result = upsert_market_data(records)
    assert result.upserted_count + result.modified_count >= 1

    rows = get_market_data(ticker, interval="1d")
    assert len(rows) >= 1
    assert rows[0]["close"] == 103.0

    latest = get_latest_timestamp(ticker, "1d")
    assert latest is not None

    deleted = delete_market_data(ticker, interval="1d")
    assert deleted >= 1


def test_market_data_idempotent_upsert():
    ticker = "_TEST_MSFT"
    ts = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rec = {
        "ticker": ticker,
        "interval": "1d",
        "timestamp": ts,
        "open": 200.0,
        "high": 210.0,
        "low": 198.0,
        "close": 205.0,
        "volume": 500_000,
        "source": "test",
        "validation_status": "ok",
    }
    upsert_market_data([rec])
    upsert_market_data([{**rec, "close": 206.0}])  # same key, updated close
    rows = get_market_data(ticker, interval="1d")
    # unique key prevents duplicates
    assert len(rows) == 1
    assert rows[0]["close"] == 206.0
    delete_market_data(ticker)


def test_company_metadata():
    doc = {
        "ticker": "_TEST_META",
        "short_name": "Meta Test",
        "primary_category": "Major technology platforms",
    }
    upsert_company_metadata(doc)
    loaded = get_company_metadata("_TEST_META")
    assert loaded is not None
    assert loaded["short_name"] == "Meta Test"


def test_predictions_and_refresh_status():
    pred_id = save_prediction(
        {
            "ticker": "_TEST_NVDA",
            "horizon": 5,
            "predicted_value": 0.01,
            "model_id": "test_model",
            "model_name": "test",
            "input_cutoff": datetime.utcnow(),
        }
    )
    assert pred_id
    preds = get_predictions(ticker="_TEST_NVDA", horizon=5, limit=5)
    assert len(preds) >= 1

    update_refresh_status(
        "_TEST_NVDA",
        "1d",
        success=True,
        last_timestamp=datetime.utcnow(),
        records_written=1,
    )
    status = get_refresh_status(ticker="_TEST_NVDA", interval="1d")
    assert len(status) >= 1
    assert status[0]["success"] is True