"""
Table formatting and metric-card helpers for Streamlit.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


def style_dataframe(
    df: pd.DataFrame,
    *,
    float_cols: Optional[List[str]] = None,
    pct_cols: Optional[List[str]] = None,
    precision: int = 4,
) -> pd.DataFrame:
    """
    Return a copy with friendly number formatting applied via Styler
    when possible; otherwise a plain rounded DataFrame.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    float_cols = float_cols or [
        c for c in out.select_dtypes(include="number").columns
        if c not in (pct_cols or [])
    ]
    pct_cols = pct_cols or []

    try:
        styler = out.style
        if float_cols:
            styler = styler.format({c: f"{{:.{precision}f}}" for c in float_cols if c in out.columns})
        if pct_cols:
            styler = styler.format({c: "{:.2%}" for c in pct_cols if c in out.columns})
        return styler
    except Exception:
        # Fallback: plain rounded frame
        for c in float_cols:
            if c in out.columns:
                out[c] = out[c].round(precision)
        return out


def metrics_cards(
    metrics: Dict[str, Any],
    *,
    columns: int = 4,
    title: Optional[str] = None,
) -> None:
    """
    Render a row of st.metric cards from a plain dictionary.
    """
    if title:
        st.subheader(title)
    if not metrics:
        st.info("No metrics available.")
        return

    items = list(metrics.items())
    cols = st.columns(min(columns, len(items)))
    for i, (label, value) in enumerate(items):
        col = cols[i % len(cols)]
        if isinstance(value, float):
            display = f"{value:.4f}"
        else:
            display = str(value) if value is not None else "—"
        col.metric(label=label.replace("_", " ").title(), value=display)


def show_dataframe(
    df: pd.DataFrame,
    *,
    height: int = 350,
    use_container_width: bool = True,
) -> None:
    """Thin wrapper around st.dataframe with sensible defaults."""
    if df is None or df.empty:
        st.info("No data to display.")
        return
    st.dataframe(df, height=height, use_container_width=use_container_width)