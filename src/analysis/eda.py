# src/analysis/eda.py
"""
Exploratory Data Analysis helpers.
All nested structures use string keys only.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _to_python(obj: Any) -> Any:
    """Convert numpy/pandas scalars to plain Python types."""
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    if isinstance(obj, (np.floating, np.integer)):
        return float(obj) if isinstance(obj, np.floating) else int(obj)
    if pd.isna(obj):
        return None
    return obj


def summary_statistics(
    df: pd.DataFrame,
    price_col: str = "close",
    return_col: str = "ret_1d",
) -> Dict[str, Any]:
    if df.empty:
        return {}

    px = df[price_col].dropna()
    rets = (
        df[return_col].dropna()
        if return_col in df.columns
        else px.pct_change().dropna()
    )

    def _f(x):
        return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)

    stats = {
        "n_obs": int(len(px)),
        "start_date": px.index.min().isoformat() if len(px) else None,
        "end_date": px.index.max().isoformat() if len(px) else None,
        "last_price": _f(px.iloc[-1]) if len(px) else None,
        "mean_return": _f(rets.mean()) if len(rets) else None,
        "std_return": _f(rets.std()) if len(rets) else None,
        "skew": _f(rets.skew()) if len(rets) else None,
        "kurtosis": _f(rets.kurtosis()) if len(rets) else None,
        "min_return": _f(rets.min()) if len(rets) else None,
        "max_return": _f(rets.max()) if len(rets) else None,
        "total_return": _f(px.iloc[-1] / px.iloc[0] - 1) if len(px) > 1 else None,
        "max_drawdown": _f(_max_drawdown(px)) if len(px) > 1 else None,
        "annualized_vol": _f(rets.std() * np.sqrt(252)) if len(rets) else None,
    }
    return stats


def run_eda(
    df: pd.DataFrame,
    ticker: str,
    price_col: str = "close",
) -> Dict[str, Any]:
    if "ret_1d" not in df.columns:
        df = df.copy()
        df["ret_1d"] = df[price_col].pct_change()

    stats = summary_statistics(df, price_col=price_col)

    # Monthly returns – force string keys at every level
    monthly_table: Dict[str, Dict[str, Any]] = {}
    try:
        monthly = (
            df[price_col]
            .resample("ME")
            .last()
            .pct_change()
            .dropna()
        )
        if not monthly.empty:
            monthly.index = monthly.index.to_period("M")
            for ts, val in monthly.items():
                year = str(int(ts.year))
                month = str(int(ts.month))
                monthly_table.setdefault(year, {})[month] = (
                    None if pd.isna(val) else float(val)
                )
    except Exception as exc:
        logger.warning("Monthly returns failed for %s: %s", ticker, exc)

    result = {
        "ticker": str(ticker).upper(),
        "analysis_type": "eda",
        "as_of": df.index.max().isoformat() if len(df) else None,
        "summary": stats,
        "monthly_returns": monthly_table,
    }
    return result


def _max_drawdown(prices: pd.Series) -> float:
    roll_max = prices.cummax()
    dd = prices / roll_max - 1.0
    return float(dd.min())