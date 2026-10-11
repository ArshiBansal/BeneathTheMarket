"""
Cross-company and cross-category comparison utilities.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config.tickers import get_primary_category

logger = logging.getLogger(__name__)


def compare_tickers(
    price_dict: Dict[str, pd.Series],
    *,
    windows: List[int] = (21, 63, 252),
    risk_free_rate: float = 0.0,
) -> pd.DataFrame:
    """
    Build a comparison table for a set of tickers.

    Columns
    -------
    ticker, category,
    total_return_{w}d, vol_{w}d, sharpe_{w}d,
    max_drawdown, last_price, n_obs
    """
    rows = []
    for ticker, prices in price_dict.items():
        if prices is None or prices.empty or len(prices) < 2:
            continue

        prices = prices.dropna().sort_index()
        rets = prices.pct_change().dropna()

        row: Dict[str, Any] = {
            "ticker": ticker,
            "category": get_primary_category(ticker),
            "last_price": float(prices.iloc[-1]),
            "n_obs": len(prices),
        }

        for w in windows:
            if len(rets) < w:
                row[f"total_return_{w}d"] = np.nan
                row[f"vol_{w}d"] = np.nan
                row[f"sharpe_{w}d"] = np.nan
                continue

            window_rets = rets.iloc[-w:]
            total_ret = float((1 + window_rets).prod() - 1)
            vol = float(window_rets.std() * np.sqrt(252))
            excess = window_rets.mean() * 252 - risk_free_rate
            sharpe = excess / vol if vol > 0 else np.nan

            row[f"total_return_{w}d"] = total_ret
            row[f"vol_{w}d"] = vol
            row[f"sharpe_{w}d"] = sharpe

        # Max drawdown over full history
        roll_max = prices.cummax()
        dd = prices / roll_max - 1.0
        row["max_drawdown"] = float(dd.min())

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows).set_index("ticker")
    logger.debug("Comparison table built for %d tickers", len(result))
    return result


def category_summary(
    comparison_df: pd.DataFrame,
    metric: str = "total_return_63d",
) -> pd.DataFrame:
    """
    Aggregate a comparison table by primary category.

    Returns mean, median, std and count for the chosen metric.
    """
    if comparison_df.empty:
        return pd.DataFrame()

    if "category" not in comparison_df.columns:
        raise KeyError("comparison_df must contain a 'category' column")

    if metric not in comparison_df.columns:
        raise KeyError(f"Metric '{metric}' not found in comparison_df")

    grouped = (
        comparison_df.groupby("category")[metric]
        .agg(["mean", "median", "std", "count"])
    )
    grouped.columns = [f"{metric}_{c}" for c in grouped.columns]
    return grouped.sort_values(f"{metric}_mean", ascending=False)


def rank_tickers(
    comparison_df: pd.DataFrame,
    metric: str = "sharpe_63d",
    ascending: bool = False,
    top_n: Optional[int] = None,
) -> pd.DataFrame:
    """
    Return tickers ranked by a chosen metric.
    """
    if comparison_df.empty:
        return pd.DataFrame()

    if metric not in comparison_df.columns:
        raise KeyError(f"Metric '{metric}' not found")

    ranked = (
        comparison_df[[metric, "category"]]
        .dropna()
        .sort_values(metric, ascending=ascending)
    )
    if top_n is not None:
        ranked = ranked.head(top_n)
    ranked = ranked.copy()
    ranked["rank"] = range(1, len(ranked) + 1)
    return ranked