"""
Operational market-regime label construction.

Labels are derived only from past information (no look-ahead bias).
The definitions are deliberately simple and fully documented so that
they can be audited and changed during the feasibility phase.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

from config.constants import REGIME_LABELS

logger = logging.getLogger(__name__)


def build_regime_labels(
    df: pd.DataFrame,
    price_col: str = "close",
    *,
    trend_window: int = 21,
    vol_window: int = 21,
    trend_threshold: float = 0.03,
    vol_threshold: float = 0.25,
    high_vol_percentile: float = 0.75,
) -> pd.DataFrame:
    """
    Attach a discrete regime label to every row.

    Regime logic (all causal)
    -------------------------
    1. Compute trailing trend = total return over `trend_window`.
    2. Compute trailing annualized volatility over `vol_window`.
    3. Label rules (applied in order):
       - high_vol  if vol > max(vol_threshold, rolling 75th percentile)
       - bull      if trend > +trend_threshold
       - bear      if trend < -trend_threshold
       - sideways  otherwise

    Returns
    -------
    pd.DataFrame
        Original frame + columns:
        - regime_trend
        - regime_vol
        - regime               (final string label)
        - regime_id            (integer encoding)
    """
    if price_col not in df.columns:
        raise KeyError(f"Column '{price_col}' not found")

    out = df.copy()
    px = out[price_col].astype(float)

    # Trailing trend (simple return)
    trend = px.pct_change(trend_window)
    out["regime_trend"] = trend

    # Trailing annualized volatility
    ret = px.pct_change()
    vol = ret.rolling(vol_window).std() * np.sqrt(252)
    out["regime_vol"] = vol

    # Dynamic high-vol threshold (expanding percentile to stay causal)
    vol_pct = vol.expanding(min_periods=vol_window).quantile(high_vol_percentile)
    high_vol_mask = vol > np.maximum(vol_threshold, vol_pct)

    # Final label
    regime = pd.Series(index=out.index, dtype=object)
    regime[:] = REGIME_LABELS["sideways"]

    regime[trend > trend_threshold] = REGIME_LABELS["bull"]
    regime[trend < -trend_threshold] = REGIME_LABELS["bear"]
    regime[high_vol_mask] = REGIME_LABELS["high_vol"]   # highest priority

    out["regime"] = regime

    # Integer encoding (stable order)
    label_to_id = {v: i for i, v in enumerate(REGIME_LABELS.values())}
    out["regime_id"] = out["regime"].map(label_to_id)

    logger.debug(
        "Regime labels built – distribution:\n%s",
        out["regime"].value_counts(dropna=False).to_dict(),
    )
    return out


def regime_transition_matrix(
    labels: pd.Series,
) -> pd.DataFrame:
    """
    Compute an empirical transition-count matrix from a regime series.
    Useful for evaluation / interpretability.
    """
    prev = labels.shift(1)
    ct = pd.crosstab(prev, labels, dropna=False)
    return ct