"""
Exploratory Data Analysis helpers for single tickers and the full universe.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def summary_statistics(
    df: pd.DataFrame,
    price_col: str = "close",
    return_col: str = "ret_1d",
) -> Dict[str, Any]:
    """
    Compute a compact set of descriptive statistics for one ticker.

    Returns a plain dict that is easy to store in MongoDB or display
    in Streamlit / notebooks.
    """
    if df.empty:
        return {}

    px = df[price_col].dropna()
    rets = df[return_col].dropna() if return_col in df.columns else px.pct_change().dropna()

    stats = {
        "n_obs": int(len(px)),
        "start_date": px.index.min().isoformat() if len(px) else None,
        "end_date": px.index.max().isoformat() if len(px) else None,
        "last_price": float(px.iloc[-1]) if len(px) else None,
        "mean_return": float(rets.mean()) if len(rets) else None,
        "std_return": float(rets.std()) if len(rets) else None,
        "skew": float(rets.skew()) if len(rets) else None,
        "kurtosis": float(rets.kurtosis()) if len(rets) else None,
        "min_return": float(rets.min()) if len(rets) else None,
        "max_return": float(rets.max()) if len(rets) else None,
        "total_return": float(px.iloc[-1] / px.iloc[0] - 1) if len(px) > 1 else None,
        "max_drawdown": float(_max_drawdown(px)) if len(px) > 1 else None,
        "annualized_vol": float(rets.std() * np.sqrt(252)) if len(rets) else None,
    }
    return stats


def run_eda(
    df: pd.DataFrame,
    ticker: str,
    price_col: str = "close",
) -> Dict[str, Any]:
    """
    Full EDA package for a single ticker.

    Returns a nested dictionary ready for storage in analysis_results
    or for display.
    """
    if "ret_1d" not in df.columns:
        df = df.copy()
        df["ret_1d"] = df[price_col].pct_change()

    stats = summary_statistics(df, price_col=price_col)

    # Monthly return table (year × month)
    monthly = (
        df[price_col]
        .resample("M")
        .last()
        .pct_change()
        .dropna()
    )
    monthly.index = monthly.index.to_period("M")
    monthly_table = monthly.groupby([monthly.index.year, monthly.index.month]).first()
    monthly_table = monthly_table.unstack(level=1)

    result = {
        "ticker": ticker.upper(),
        "analysis_type": "eda",
        "as_of": df.index.max().isoformat() if len(df) else None,
        "summary": stats,
        "monthly_returns": monthly_table.replace({np.nan: None}).to_dict()
        if not monthly_table.empty
        else {},
    }
    logger.debug("EDA completed for %s – %d observations", ticker, stats.get("n_obs", 0))
    return result


def _max_drawdown(prices: pd.Series) -> float:
    """Peak-to-trough maximum drawdown."""
    roll_max = prices.cummax()
    dd = prices / roll_max - 1.0
    return float(dd.min())