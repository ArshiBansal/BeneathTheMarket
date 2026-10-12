"""
Streamlit entry point.

Launch from the project root:

    streamlit run app/main.py

Purpose-based pages live under app/pages/ and are discovered
automatically by Streamlit (multipage app).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, TICKERS, CATEGORIES
from app.components.status_banner import status_banner
from app.services.data_service import DataService

st.set_page_config(
    page_title="Tech & Fintech Market Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("Market Intelligence")
    st.caption("Technology & Fintech · Regime Analyzer")
    st.markdown("---")
    st.markdown(
        """
**Pages**

1. Market Overview  
2. Cross-Company Comparison  
3. Regime Intelligence  
4. Forecasting  
5. Risk Analysis  
6. NLP Insights  
7. Data Status  
"""
    )
    st.markdown("---")
    st.caption(f"DB: `{settings.MONGODB_DB_NAME}`")
    st.caption(f"URI: `{settings.MONGODB_URI}`")
    st.caption("Local MongoDB only · No Atlas")
    st.caption("Not investment advice")

st.title("Technology & Fintech Market Intelligence")
st.subheader("and Regime Analyzer")

st.markdown(
    """
An intermediate AI/ML/DL/NLP system for multi-company market analysis,
regime discovery and forecasting, using **yfinance** data and a
**local MongoDB** persistence layer.

Use the sidebar to open a purpose-based section.
"""
)

# Freshness banner (never claims real-time)
status_banner()

# Quick stats
col1, col2, col3, col4 = st.columns(4)
try:
    cov = DataService.coverage_summary()
    col1.metric("Tickers in universe", len(TICKERS))
    col2.metric("Categories", len(CATEGORIES))
    col3.metric("With stored data", cov.get("n_present", "—"))
    col4.metric("Missing data", cov.get("n_missing", "—"))
except Exception as exc:
    st.warning(f"Could not load coverage summary: {exc}")

st.markdown("---")

st.markdown(
    """
### Design principles

| Principle | Implementation |
|-----------|----------------|
| Independent app | Runs without executing any notebook |
| Shared persistence | Local MongoDB via PyMongo |
| No news NLP | Company / category descriptions only |
| Transparent forecasts | Horizon, model id, cutoff, uncertainty notes |
| Chronological evaluation | Research notebooks use time-ordered splits |

### Getting started

1. Ensure local `mongod` is running on `localhost:27017`
2. Run `python scripts/init_mongodb.py --seed-metadata`
3. Run `python scripts/backfill_market_data.py --from-validated`
4. Open the pages from the sidebar
"""
)

st.markdown("---")
st.caption(
    "Academic / research use only. Historical metrics do not guarantee "
    "future performance. This application does not execute trades or "
    "provide personalised investment advice."
)