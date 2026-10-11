"""
Datetime helpers that keep everything timezone-aware and consistent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

import pandas as pd


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def to_utc_aware(
    dt: Union[datetime, pd.Timestamp, str, None],
) -> Optional[datetime]:
    """
    Convert a variety of inputs into a timezone-aware UTC datetime.

    - None → None
    - naïve datetime / Timestamp → assumed UTC and made aware
    - already-aware → converted to UTC
    - ISO string → parsed then converted
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        dt = pd.to_datetime(dt, utc=True).to_pydatetime()

    if isinstance(dt, pd.Timestamp):
        if dt.tzinfo is None:
            dt = dt.tz_localize("UTC")
        else:
            dt = dt.tz_convert("UTC")
        return dt.to_pydatetime()

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    raise TypeError(f"Cannot convert type {type(dt)} to UTC datetime")


def ensure_datetime(
    value: Union[datetime, pd.Timestamp, str, None],
    *,
    default: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Best-effort conversion used by data-access layers.
    Returns `default` when conversion fails or value is None.
    """
    try:
        return to_utc_aware(value)
    except Exception:
        return default


def trading_days_between(
    start: Union[datetime, pd.Timestamp],
    end: Union[datetime, pd.Timestamp],
) -> int:
    """
    Approximate number of trading days between two dates
    (weekdays only – ignores exchange holidays).
    """
    start = pd.Timestamp(to_utc_aware(start)).normalize()
    end = pd.Timestamp(to_utc_aware(end)).normalize()
    if end < start:
        start, end = end, start
    return int(len(pd.bdate_range(start, end)) - 1)