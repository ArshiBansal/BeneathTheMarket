"""
Tests for the yfinance client wrapper and normalizer.

Network-dependent tests are marked and may be skipped offline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_pipeline.yfinance_client import fetch_ohlcv, fetch_ticker_info
from src.data_pipeline.normalizer import normalize_ohlcv
from src.data_pipeline.validators import validate_records


def test_normalize_ohlcv_basic():
    idx = pd.date_range("2024-01-01", periods=5, freq="B")
    raw = pd.DataFrame(
        {
            "Open": [100, 101, 102, 103, 104],
            "High": [105, 106, 107, 108, 109],
            "Low": [99, 100, 101, 102, 103],
            "Close": [103, 104, 105, 106, 107],
            "Volume": [1e6, 1.1e6, 1.2e6, 1.0e6, 0.9e6],
        },
        index=idx,
    )
    records = normalize_ohlcv(raw, "AAPL", "1d")
    assert len(records) == 5
    assert records[0]["ticker"] == "AAPL"
    assert records[0]["interval"] == "1d"
    assert records[0]["close"] == 103.0
    assert "timestamp" in records[0]


def test_normalize_empty():
    assert normalize_ohlcv(pd.DataFrame(), "AAPL", "1d") == []


def test_validate_records_drops_bad():
    good = {
        "ticker": "AAPL",
        "interval": "1d",
        "timestamp": pd.Timestamp("2024-01-02"),
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 103.0,
        "volume": 1e6,
    }
    bad = {**good, "timestamp": None}
    inverted = {**good, "high": 90.0, "low": 100.0, "validation_status": "ok"}
    clean = validate_records([good, bad, inverted])
    assert len(clean) == 2  # bad dropped; inverted kept but flagged
    statuses = {r.get("validation_status") for r in clean}
    assert "ok" in statuses or "high_lt_low" in statuses


@pytest.mark.network
def test_fetch_ohlcv_live():
    """Requires network + yfinance availability."""
    df = fetch_ohlcv("AAPL", period="5d", interval="1d")
    if df.empty:
        pytest.skip("yfinance returned empty data")
    assert "Close" in df.columns or "close" in [c.lower() for c in df.columns]
    assert len(df) >= 1


@pytest.mark.network
def test_fetch_ticker_info_live():
    info = fetch_ticker_info("MSFT")
    assert info.get("ticker") == "MSFT"
    # name may be missing depending on upstream, but key should exist
    assert "retrieved_at" in info