"""
Correlation and co-movement analysis.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def correlation_matrix(
    price_dict: Dict[str, pd.Series],
    method: str = "pearson",
    min_periods: int = 30,
) -> pd.DataFrame:
    """
    Build a full correlation matrix from a dictionary of price series.

    Parameters
    ----------
    price_dict : {ticker: price_series}
    method : 'pearson' | 'spearman' | 'kendall'
    min_periods : minimum overlapping observations required

    Returns
    -------
    pd.DataFrame  (tickers × tickers)
    """
    if not price_dict:
        return pd.DataFrame()

    prices = pd.DataFrame(price_dict)
    rets = prices.pct_change()
    corr = rets.corr(method=method, min_periods=min_periods)
    logger.debug("Correlation matrix computed for %d tickers", len(corr))
    return corr


def rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 63,
    min_periods: Optional[int] = None,
) -> pd.Series:
    """
    Rolling Pearson correlation between two return series.
    """
    min_periods = min_periods or max(10, window // 3)
    rets_a = series_a.pct_change()
    rets_b = series_b.pct_change()
    return rets_a.rolling(window, min_periods=min_periods).corr(rets_b)


def average_correlation(
    corr_matrix: pd.DataFrame,
    exclude_diagonal: bool = True,
) -> float:
    """
    Mean pairwise correlation (optionally excluding the diagonal of 1s).
    """
    if corr_matrix.empty:
        return np.nan
    vals = corr_matrix.values
    if exclude_diagonal:
        mask = ~np.eye(vals.shape[0], dtype=bool)
        return float(vals[mask].mean())
    return float(vals.mean())


def correlation_summary(
    price_dict: Dict[str, pd.Series],
    method: str = "pearson",
) -> Dict[str, any]:
    """
    High-level summary useful for reports and MongoDB storage.
    """
    corr = correlation_matrix(price_dict, method=method)
    if corr.empty:
        return {}

    avg = average_correlation(corr)
    # Most / least correlated pair (off-diagonal)
    np.fill_diagonal(corr.values, np.nan)
    max_pair = corr.stack().idxmax()
    min_pair = corr.stack().idxmin()

    return {
        "n_tickers": len(corr),
        "average_correlation": avg,
        "max_pair": {"tickers": list(max_pair), "value": float(corr.loc[max_pair])},
        "min_pair": {"tickers": list(min_pair), "value": float(corr.loc[min_pair])},
        "matrix": corr.replace({np.nan: None}).to_dict(),
    }