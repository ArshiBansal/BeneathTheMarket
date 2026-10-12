"""
Unit tests for causal feature engineering.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.features.returns import add_returns, cumulative_return
from src.features.volatility import add_volatility
from src.features.technical import add_technical
from src.features.regime_labels import build_regime_labels
from src.features import build_feature_matrix


@pytest.fixture
def price_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 120
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    close = 100 * np.cumprod(1 + rng.normal(0.0005, 0.015, n))
    return pd.DataFrame(
        {
            "open": close * 0.99,
            "high": close * 1.01,
            "low": close * 0.98,
            "close": close,
            "volume": rng.integers(1e5, 1e6, n),
        },
        index=idx,
    )


def test_add_returns(price_df):
    out = add_returns(price_df)
    assert "ret_1d" in out.columns
    assert "log_ret_5d" in out.columns
    # first row of ret_1d must be NaN (no look-ahead)
    assert pd.isna(out["ret_1d"].iloc[0])


def test_add_volatility(price_df):
    out = add_volatility(price_df)
    assert "vol_21d" in out.columns
    assert "dd_from_peak" in out.columns
    assert out["dd_from_peak"].max() <= 0.0 + 1e-9


def test_add_technical(price_df):
    out = add_technical(price_df)
    assert "sma_21" in out.columns
    assert "rsi_14" in out.columns
    assert "macd" in out.columns
    # RSI bounds
    rsi = out["rsi_14"].dropna()
    assert rsi.min() >= 0 - 1e-6
    assert rsi.max() <= 100 + 1e-6


def test_regime_labels(price_df):
    out = build_regime_labels(price_df)
    assert "regime" in out.columns
    assert "regime_id" in out.columns
    assert out["regime"].notna().any()


def test_build_feature_matrix(price_df):
    out = build_feature_matrix(price_df, dropna=True)
    assert len(out) > 0
    assert "ret_1d" in out.columns
    assert "vol_21d" in out.columns


def test_cumulative_return(price_df):
    r = cumulative_return(price_df)
    assert isinstance(r, float)
    assert not np.isnan(r)


def test_no_lookahead_returns(price_df):
    """Ensure return at t uses only prices up to t."""
    out = add_returns(price_df, windows=[1])
    # ret_1d[t] = close[t]/close[t-1] - 1
    manual = price_df["close"].pct_change(1)
    pd.testing.assert_series_equal(
        out["ret_1d"], manual, check_names=False
    )