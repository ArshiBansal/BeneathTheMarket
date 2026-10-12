"""
Data-freshness status banner shown at the top of Streamlit pages.

Never labels delayed or missing data as real-time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import streamlit as st

from app.services.data_service import DataService


def _parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def status_banner(
    *,
    tickers: Optional[List[str]] = None,
    interval: str = "1d",
    max_age_hours: float = 36.0,
) -> None:
    """
    Render a compact freshness summary.

    Parameters
    ----------
    tickers : optional subset to check; defaults to a light sample.
    interval : bar interval tracked in refresh_status.
    max_age_hours : threshold beyond which data is flagged as stale.
    """
    try:
        status_docs = DataService.get_freshness(interval=interval)
    except Exception as exc:
        st.warning(f"Could not read refresh status: {exc}")
        return

    if not status_docs:
        st.info(
            "No refresh-status records yet. "
            "Run a backfill or daily update to populate data freshness."
        )
        return

    now = datetime.now(timezone.utc)
    fresh, stale, failed = 0, 0, 0
    latest_success: Optional[datetime] = None

    for doc in status_docs:
        if tickers and doc.get("ticker") not in tickers:
            continue
        if not doc.get("success", False):
            failed += 1
            continue
        ts = _parse_ts(doc.get("last_success_at") or doc.get("last_data_timestamp"))
        if ts is None:
            stale += 1
            continue
        age_h = (now - ts).total_seconds() / 3600.0
        if age_h <= max_age_hours:
            fresh += 1
        else:
            stale += 1
        if latest_success is None or ts > latest_success:
            latest_success = ts

    # Build message – never claim “live” or “real-time”
    parts = []
    if latest_success:
        parts.append(f"Last successful update: **{latest_success.strftime('%Y-%m-%d %H:%M UTC')}**")
    parts.append(f"Fresh (≤{max_age_hours:.0f}h): **{fresh}**")
    parts.append(f"Stale: **{stale}**")
    if failed:
        parts.append(f"Failed: **{failed}**")

    msg = " · ".join(parts)

    if failed and fresh == 0:
        st.error(f"Data status — {msg}. Data may be unavailable.")
    elif stale > fresh:
        st.warning(f"Data status — {msg}. Some series may be delayed.")
    else:
        st.success(f"Data status — {msg}. (Not real-time.)")


def single_ticker_freshness(ticker: str, interval: str = "1d") -> None:
    """Compact caption for a single ticker."""
    ts = DataService.last_data_timestamp(ticker, interval=interval)
    if ts is None:
        st.caption(f"{ticker}: no stored data")
        return
    st.caption(
        f"{ticker}: last bar **{ts.strftime('%Y-%m-%d %H:%M')}** (stored, not live)"
    )