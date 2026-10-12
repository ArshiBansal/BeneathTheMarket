"""
Data status – coverage, freshness and pipeline health.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from app.services.data_service import DataService
from app.components.filters import ticker_selector, category_selector
from app.components.tables import show_dataframe, metrics_cards
from app.components.status_banner import status_banner

st.set_page_config(page_title="Data Status", page_icon="🗄️", layout="wide")
st.title("Data Status")
st.caption(
    "Freshness and coverage of the local MongoDB store. "
    "Timestamps reflect last successful retrieval — not a live feed."
)

status_banner(max_age_hours=36)

# Coverage summary
st.subheader("Coverage summary")
cov = DataService.coverage_summary()
metrics_cards(
    {
        "Requested": cov["n_requested"],
        "With data": cov["n_present"],
        "Missing": cov["n_missing"],
        "Interval": cov["interval"],
    },
    columns=4,
)

if cov["missing"]:
    st.warning(f"Missing tickers: {', '.join(cov['missing'][:20])}"
               + (" …" if len(cov["missing"]) > 20 else ""))

# Refresh status table
st.subheader("Refresh status (per ticker)")
status_docs = DataService.get_freshness(interval="1d")
if status_docs:
    sdf = pd.DataFrame(status_docs)
    cols = [
        c for c in [
            "ticker", "interval", "success", "last_success_at",
            "last_data_timestamp", "records_written", "last_error",
        ]
        if c in sdf.columns
    ]
    show_dataframe(sdf[cols].sort_values("ticker"), height=400)
else:
    st.info("No refresh_status records. Run scripts/backfill_market_data.py first.")

# On-demand light refresh
st.subheader("On-demand recent refresh")
st.caption("Fetches a short recent window from yfinance and upserts into MongoDB.")
cat = category_selector(key="ds_cat")
ticker = ticker_selector(category=cat, key="ds_ticker")
lookback = st.slider("Lookback days", 3, 15, 5)
if st.button("Refresh selected ticker", type="primary") and ticker:
    with st.spinner(f"Refreshing {ticker}..."):
        n = DataService.refresh_ticker_recent(ticker, lookback_days=lookback)
    if n:
        st.success(f"Wrote/updated {n} records for {ticker}.")
    else:
        st.warning(f"No records written for {ticker}. Check logs / upstream availability.")

# Connection info
with st.expander("Connection info"):
    st.write(
        {
            "MongoDB URI": settings.MONGODB_URI,
            "Database": settings.MONGODB_DB_NAME,
            "Processed dir": str(settings.PROCESSED_DATA_DIR),
            "Note": "Local MongoDB only — Atlas is not used.",
        }
    )