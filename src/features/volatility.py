"""
Volatility and drawdown features.
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_VOL_WINDOWS: List[int] = [5, 10, 21, 63]


def add_volatility(
    df: pd.DataFrame,
    price_col: str = "close",
    windows: List[int] | None = None,
    annualize: bool = True,
    trading_days: int = 252,
) -> pd.DataFrame:
    """
    Append rolling realized-volatility and maximum-drawdown features.

    Columns created
    ---------------
    vol_{w}d          rolling std of 1-day returns (optionally annualized)
    max_dd_{w}d       maximum drawdown over the trailing window
    dd_from_peak      current drawdown from the expanding peak
    """
    if price_col not in df.columns:
        raise KeyError(f"Column '{price_col}' not found")

    windows = windows or DEFAULT_VOL_WINDOWS
    out = df.copy()
    ret = out[price_col].pct_change()

    for w in windows:
        # Realized volatility
        vol = ret.rolling(w).std()
        if annualize:
            vol = vol * np.sqrt(trading_days)
        out[f"vol_{w}d"] = vol

        # Maximum drawdown over the window
        roll_max = out[price_col].rolling(w, min_periods=1).max()
        dd = out[price_col] / roll_max - 1.0
        out[f"max_dd_{w}d"] = dd.rolling(w, min_periods=1).min()

    # Expanding drawdown from peak (whole history up to each point)
    expanding_max = out[price_col].expanding(min_periods=1).max()
    out["dd_from_peak"] = out[price_col] / expanding_max - 1.0

    logger.debug("Added volatility / drawdown features for windows %s", windows)
    return out


def realized_volatility(
    series: pd.Series,
    window: int = 21,
    annualize: bool = True,
    trading_days: int = 252,
) -> pd.Series:
    """Standalone helper that returns a volatility Series."""
    vol = series.pct_change().rolling(window).std()
    if annualize:
        vol = vol * np.sqrt(trading_days)
    return vol