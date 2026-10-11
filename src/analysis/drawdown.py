"""
Drawdown analysis and underwater-curve helpers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def underwater_curve(
    prices: pd.Series,
) -> pd.Series:
    """
    Return the running drawdown series (prices / expanding max - 1).
    """
    roll_max = prices.cummax()
    return prices / roll_max - 1.0


def drawdown_stats(
    prices: pd.Series,
    top_n: int = 5,
) -> Dict[str, Any]:
    """
    Comprehensive drawdown statistics for a single price series.

    Returns
    -------
    dict with:
        max_drawdown, max_drawdown_date,
        avg_drawdown, median_drawdown,
        top_drawdowns (list of dicts),
        recovery_times (days)
    """
    if prices.empty or len(prices) < 2:
        return {}

    dd = underwater_curve(prices)
    max_dd = float(dd.min())
    max_dd_date = dd.idxmin()

    # Identify distinct drawdown episodes (simple peak-to-trough-to-recovery)
    episodes = _extract_drawdown_episodes(prices, dd)

    top = sorted(episodes, key=lambda x: x["depth"])[:top_n]

    recovery_days = [
        e["recovery_days"] for e in episodes if e["recovery_days"] is not None
    ]

    stats = {
        "max_drawdown": max_dd,
        "max_drawdown_date": max_dd_date.isoformat() if max_dd_date else None,
        "avg_drawdown": float(dd.mean()),
        "median_drawdown": float(dd.median()),
        "n_episodes": len(episodes),
        "top_drawdowns": top,
        "avg_recovery_days": float(np.mean(recovery_days)) if recovery_days else None,
        "max_recovery_days": int(np.max(recovery_days)) if recovery_days else None,
    }
    logger.debug("Drawdown stats computed – max DD = %.2f%%", max_dd * 100)
    return stats


def _extract_drawdown_episodes(
    prices: pd.Series,
    dd: pd.Series,
) -> List[Dict[str, Any]]:
    """
    Very simple episode detector:
    - A new episode starts when dd becomes negative after having been ≥ 0
    - Episode ends when price recovers to the previous peak (dd returns to 0)
    """
    episodes = []
    in_dd = False
    start_idx = None
    peak_price = None

    for i, (ts, val) in enumerate(dd.items()):
        if not in_dd and val < 0:
            in_dd = True
            start_idx = ts
            peak_price = prices.iloc[i - 1] if i > 0 else prices.iloc[0]
        elif in_dd and val >= 0:
            # recovered
            end_idx = ts
            trough_idx = dd.loc[start_idx:end_idx].idxmin()
            depth = float(dd.loc[trough_idx])
            recovery_days = (end_idx - start_idx).days
            episodes.append(
                {
                    "start": start_idx.isoformat(),
                    "trough": trough_idx.isoformat(),
                    "end": end_idx.isoformat(),
                    "depth": depth,
                    "recovery_days": recovery_days,
                }
            )
            in_dd = False

    # Handle open (unrecovered) drawdown at the end
    if in_dd and start_idx is not None:
        trough_idx = dd.loc[start_idx:].idxmin()
        episodes.append(
            {
                "start": start_idx.isoformat(),
                "trough": trough_idx.isoformat(),
                "end": None,
                "depth": float(dd.loc[trough_idx]),
                "recovery_days": None,
            }
        )

    return episodes