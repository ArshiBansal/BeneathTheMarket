"""
Exploratory and comparative analysis package.

Provides higher-level analytics that sit on top of the feature
and data layers:

- eda.py               classic single-ticker & universe EDA
- correlation.py       correlation matrices and rolling co-movement
- drawdown.py          drawdown statistics and underwater curves
- regime_discovery.py  unsupervised regime / cluster analysis
- comparison.py        cross-company and cross-category comparison tables

Public API
----------
from src.analysis import (
    run_eda,
    correlation_matrix,
    drawdown_stats,
    discover_regimes,
    compare_tickers,
)
"""

from .eda import run_eda, summary_statistics
from .correlation import correlation_matrix, rolling_correlation
from .drawdown import drawdown_stats, underwater_curve
from .regime_discovery import discover_regimes, regime_summary
from .comparison import compare_tickers, category_summary

__all__ = [
    "run_eda",
    "summary_statistics",
    "correlation_matrix",
    "rolling_correlation",
    "drawdown_stats",
    "underwater_curve",
    "discover_regimes",
    "regime_summary",
    "compare_tickers",
    "category_summary",
]