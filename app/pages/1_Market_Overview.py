"""
Market Overview – single-ticker price, returns, drawdown and summary stats.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.data_service import DataService
from app.components.filters import category_selector, ticker_selector, date_range_selector
from app.components.charts import plot_price, plot_returns, plot_underwater, plot_ohlcv_candles
from app.components.tables import metrics_cards
from app.components.status_banner import status_banner, single_ticker_freshness
from src.features.returns import add_returns
from src.features.volatility import add_volatility
from src.analysis.eda import summary_statistics
from src.analysis.drawdown import drawdown_stats

st.set_page_config(page_title="Market Overview", page_icon="📈", layout="wide")
st.title("Market Overview")
st.caption("Historical price, returns and risk snapshot for a single ticker.")

status_banner()

# ---- Filters ----
col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    cat = category_selector(key="ov_category")
with col_b:
    ticker = ticker_selector(category=cat, key="ov_ticker")
with col_c:
    start, end = date_range_selector(default_days=730, key="ov_dates")

if not ticker:
    st.stop()

single_ticker_freshness(ticker)

# ---- Load data ----
df = DataService.load_ohlcv(
    ticker,
    start=pd.Timestamp(start) if start else None,
    end=pd.Timestamp(end) if end else None,
)
if df.empty:
    st.warning(f"No stored data for {ticker}. Run a backfill first.")
    st.stop()

df = add_returns(df)
df = add_volatility(df)

# ---- Metrics ----
stats = summary_statistics(df)
metrics_cards(
    {
        "Last price": stats.get("last_price"),
        "Total return": stats.get("total_return"),
        "Ann. volatility": stats.get("annualized_vol"),
        "Max drawdown": stats.get("max_drawdown"),
        "Observations": stats.get("n_obs"),
    },
    columns=5,
)

# ---- Charts ----
tab1, tab2, tab3 = st.tabs(["Price", "Candles", "Returns & Drawdown"])
with tab1:
    st.plotly_chart(plot_price(df, title=f"{ticker} – Close"), use_container_width=True)
with tab2:
    st.plotly_chart(plot_ohlcv_candles(df, title=f"{ticker} – OHLCV"), use_container_width=True)
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            plot_returns(df, title=f"{ticker} – Daily returns"),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            plot_underwater(df["close"], title=f"{ticker} – Underwater"),
            use_container_width=True,
        )

# ---- Drawdown table ----
with st.expander("Drawdown statistics"):
    dd = drawdown_stats(df["close"])
    st.json({k: v for k, v in dd.items() if k != "top_drawdowns"})