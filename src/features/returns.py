"""
Return-based features (simple & log returns over multiple horizons).
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default horizons in trading days
DEFAULT_RETURN_WINDOWS: List[int] = [1, 5, 10, 21]


def add_returns(
    df: pd.DataFrame,
    price_col: str = "close",
    windows: List[int] | None = None,
    prefix: str = "ret",
) -> pd.DataFrame:
    """
    Append simple and log-return columns.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain `price_col`.
    price_col : str
        Column used to compute returns (usually 'close').
    windows : list of int
        Look-back periods in bars.
    prefix : str
        Prefix for the generated column names.

    Returns
    -------
    pd.DataFrame
        Original frame with extra columns:
        - {prefix}_{w}d          simple return
        - log_{prefix}_{w}d      log return
    """
    if price_col not in df.columns:
        raise KeyError(f"Column '{price_col}' not found in DataFrame")

    windows = windows or DEFAULT_RETURN_WINDOWS
    out = df.copy()
    px = out[price_col].astype(float)

    for w in windows:
        # Simple return
        out[f"{prefix}_{w}d"] = px.pct_change(w)
        # Log return
        out[f"log_{prefix}_{w}d"] = np.log(px / px.shift(w))

    logger.debug("Added return features for windows %s", windows)
    return out


def cumulative_return(
    df: pd.DataFrame,
    price_col: str = "close",
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> float:
    """
    Compute the cumulative simple return over an optional date range.
    Useful for cross-company comparison tables.
    """
    if price_col not in df.columns:
        raise KeyError(f"Column '{price_col}' not found")

    s = df[price_col].dropna()
    if start is not None:
        s = s[s.index >= start]
    if end is not None:
        s = s[s.index <= end]
    if len(s) < 2:
        return np.nan
    return float(s.iloc[-1] / s.iloc[0] - 1.0)