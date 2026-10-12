"""
Sidebar / inline filter widgets shared across Streamlit pages.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

import streamlit as st

from config import TICKERS, CATEGORIES
from config.tickers import get_all_categories
from config.constants import FORECAST_HORIZONS


def category_selector(
    label: str = "Category",
    *,
    include_all: bool = True,
    key: str = "category_filter",
) -> Optional[str]:
    """Return selected category or None for 'All'."""
    cats = get_all_categories()
    options = (["All"] + cats) if include_all else cats
    choice = st.selectbox(label, options, key=key)
    return None if choice == "All" else choice


def ticker_selector(
    tickers: Optional[List[str]] = None,
    *,
    label: str = "Ticker",
    default: Optional[str] = None,
    key: str = "ticker_filter",
    category: Optional[str] = None,
) -> str:
    """
    Single-ticker selectbox.
    If `category` is given, restrict the list to that category.
    """
    if category and category in CATEGORIES:
        pool = CATEGORIES[category]
    else:
        pool = tickers or list(TICKERS)

    if not pool:
        st.warning("No tickers available.")
        return ""

    idx = 0
    if default and default in pool:
        idx = pool.index(default)
    return st.selectbox(label, pool, index=idx, key=key)


def multi_ticker_selector(
    tickers: Optional[List[str]] = None,
    *,
    label: str = "Tickers",
    default: Optional[List[str]] = None,
    key: str = "multi_ticker_filter",
    max_selections: int = 12,
) -> List[str]:
    """Multi-select ticker widget with a soft cap."""
    pool = tickers or list(TICKERS)
    default = default or pool[: min(5, len(pool))]
    selected = st.multiselect(label, pool, default=default, key=key)
    if len(selected) > max_selections:
        st.caption(f"Showing first {max_selections} of {len(selected)} selected.")
        return selected[:max_selections]
    return selected


def date_range_selector(
    *,
    label: str = "Date range",
    default_days: int = 365,
    key: str = "date_range",
) -> Tuple[Optional[date], Optional[date]]:
    """Return (start_date, end_date)."""
    today = date.today()
    start_default = today - timedelta(days=default_days)
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input(f"{label} – start", value=start_default, key=f"{key}_start")
    with col2:
        end = st.date_input(f"{label} – end", value=today, key=f"{key}_end")
    if start and end and start > end:
        st.warning("Start date is after end date.")
    return start, end


def horizon_selector(
    *,
    label: str = "Forecast horizon (trading days)",
    key: str = "horizon_filter",
) -> int:
    options = FORECAST_HORIZONS if FORECAST_HORIZONS else [1, 5, 10, 21]
    return st.selectbox(label, options, index=min(1, len(options) - 1), key=key)


def interval_selector(
    *,
    label: str = "Interval",
    key: str = "interval_filter",
) -> str:
    return st.selectbox(label, ["1d", "1wk", "1mo"], index=0, key=key)