"""
Cross-sectional / relative features that compare a ticker against
a market proxy or a peer set.

These features are computed on aligned dates only, never using future data.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def add_cross_company_features(
    df: pd.DataFrame,
    market_df: pd.DataFrame,
    *,
    price_col: str = "close",
    market_price_col: str = "close",
    windows: List[int] | None = None,
    market_ticker: str = "MARKET",
) -> pd.DataFrame:
    """
    Add relative-strength, correlation and beta features versus a market proxy.

    Parameters
    ----------
    df : pd.DataFrame
        Single-ticker OHLCV (+ already computed returns if available).
    market_df : pd.DataFrame
        Market-proxy series (e.g. equal-weight basket or SPY-like proxy).
        Must share a comparable DatetimeIndex.
    windows : list of int
        Rolling windows for correlation / beta.
    """
    windows = windows or [21, 63]
    out = df.copy()

    # Align on the intersection of dates
    common_idx = out.index.intersection(market_df.index)
    if len(common_idx) < 5:
        logger.warning("Too few overlapping dates for cross-company features")
        return out

    px = out.loc[common_idx, price_col].astype(float)
    mkt = market_df.loc[common_idx, market_price_col].astype(float)

    ret = px.pct_change()
    mkt_ret = mkt.pct_change()

    for w in windows:
        # Rolling correlation
        out.loc[common_idx, f"corr_market_{w}d"] = ret.rolling(w).corr(mkt_ret)

        # Rolling beta (cov / var)
        cov = ret.rolling(w).cov(mkt_ret)
        var = mkt_ret.rolling(w).var()
        out.loc[common_idx, f"beta_market_{w}d"] = cov / var.replace(0, np.nan)

        # Relative strength (cumulative return ratio over the window)
        rel = (1 + ret).rolling(w).apply(np.prod, raw=True) / \
              (1 + mkt_ret).rolling(w).apply(np.prod, raw=True)
        out.loc[common_idx, f"relative_strength_{w}d"] = rel

    logger.debug("Added cross-company features vs %s", market_ticker)
    return out


def build_market_proxy(
    price_dict: Dict[str, pd.Series],
    method: str = "equal_weight",
) -> pd.DataFrame:
    """
    Build a simple market proxy from a dictionary of {ticker: price_series}.

    method : 'equal_weight' | 'mean_return'
    Returns a DataFrame with a single 'close' column.
    """
    if not price_dict:
        raise ValueError("price_dict cannot be empty")

    # Align all series
    prices = pd.DataFrame(price_dict).dropna(how="all")
    if method == "equal_weight":
        # Normalize each series to 1 at the first valid point, then average
        normed = prices / prices.iloc[0]
        proxy = normed.mean(axis=1)
    else:  # mean daily return then cumulate
        rets = prices.pct_change()
        mean_ret = rets.mean(axis=1)
        proxy = (1 + mean_ret).cumprod()

    return pd.DataFrame({"close": proxy}, index=prices.index)