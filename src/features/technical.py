"""
Classic technical indicators (SMA, EMA, MACD, RSI, …).
All calculations are causal (use only past data).
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_technical(
    df: pd.DataFrame,
    price_col: str = "close",
    volume_col: str = "volume",
    sma_windows: List[int] | None = None,
    ema_windows: List[int] | None = None,
) -> pd.DataFrame:
    """
    Append a standard set of technical features.

    Columns created
    ---------------
    sma_{w}, ema_{w}
    macd, macd_signal, macd_hist
    rsi_14
    volume_sma_ratio_{w}
    """
    if price_col not in df.columns:
        raise KeyError(f"Column '{price_col}' not found")

    sma_windows = sma_windows or [5, 21, 63]
    ema_windows = ema_windows or [12, 26]
    out = df.copy()
    px = out[price_col].astype(float)

    # Simple moving averages
    for w in sma_windows:
        out[f"sma_{w}"] = px.rolling(w, min_periods=1).mean()

    # Exponential moving averages
    for w in ema_windows:
        out[f"ema_{w}"] = px.ewm(span=w, adjust=False).mean()

    # MACD (12, 26, 9)
    ema12 = px.ewm(span=12, adjust=False).mean()
    ema26 = px.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    out["macd"] = macd
    out["macd_signal"] = signal
    out["macd_hist"] = macd - signal

    # RSI 14
    out["rsi_14"] = _rsi(px, window=14)

    # Volume ratios (if volume present)
    if volume_col in out.columns:
        vol = out[volume_col].astype(float)
        for w in (5, 21):
            sma_vol = vol.rolling(w, min_periods=1).mean()
            out[f"volume_sma_ratio_{w}d"] = vol / sma_vol.replace(0, np.nan)
        out["volume_change_1d"] = vol.pct_change()

    logger.debug("Added technical indicators")
    return out


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Wilder’s RSI implementation."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi