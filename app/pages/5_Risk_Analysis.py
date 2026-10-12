"""
Risk analysis – volatility, drawdowns and dispersion across peers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.data_service import DataService
from app.components.filters import (
    ticker_selector,
    category_selector,
    multi_ticker_selector,
    date_range_selector,
)
from app.components.charts import plot_underwater, plot_bar_ranking
from app.components.tables import show_dataframe, metrics_cards
from app.components.status_banner import status_banner
from src.features.volatility import add_volatility
from src.analysis.drawdown import drawdown_stats
from src.analysis.comparison import compare_tickers

st.set_page_config(page_title="Risk Analysis", page_icon="⚠️", layout="wide")
st.title("Risk Analysis")
st.caption(
    "Historical volatility and drawdown statistics. "
    "These are realised measures — not guarantees of future risk."
)

status_banner()

tab1, tab2 = st.tabs(["Single ticker", "Peer comparison"])

with tab1:
    cat = category_selector(key="risk_cat")
    ticker = ticker_selector(category=cat, key="risk_ticker")
    start, end = date_range_selector(default_days=730, key="risk_dates")
    if ticker:
        df = DataService.load_ohlcv(
            ticker,
            start=pd.Timestamp(start) if start else None,
            end=pd.Timestamp(end) if end else None,
        )
        if df.empty:
            st.warning("No data.")
        else:
            df = add_volatility(df)
            dd = drawdown_stats(df["close"])
            metrics_cards(
                {
                    "Max drawdown": dd.get("max_drawdown"),
                    "Avg drawdown": dd.get("avg_drawdown"),
                    "Episodes": dd.get("n_episodes"),
                    "Avg recovery (days)": dd.get("avg_recovery_days"),
                },
                columns=4,
            )
            st.plotly_chart(
                plot_underwater(df["close"], title=f"{ticker} – Underwater curve"),
                use_container_width=True,
            )
            if "vol_21d" in df.columns:
                st.line_chart(df[["vol_21d", "vol_63d"]].dropna())

with tab2:
    pool = DataService.list_tickers()
    peers = multi_ticker_selector(pool, default=pool[:8], key="risk_peers")
    if len(peers) >= 2:
        panel = DataService.load_close_panel(peers)
        if not panel.empty:
            price_dict = {t: panel[t].dropna() for t in panel.columns}
            comp = compare_tickers(price_dict, windows=[63, 252])
            st.subheader("Risk metrics across peers")
            show_dataframe(
                comp[["vol_63d", "vol_252d", "max_drawdown", "sharpe_63d"]].round(4)
                if set(["vol_63d", "vol_252d", "max_drawdown", "sharpe_63d"]).issubset(comp.columns)
                else comp.round(4),
                height=400,
            )
            if "max_drawdown" in comp.columns:
                plot_df = comp.reset_index().rename(columns={"index": "ticker"})
                if "ticker" not in plot_df.columns:
                    plot_df["ticker"] = plot_df.index
                st.plotly_chart(
                    plot_bar_ranking(
                        plot_df,
                        value_col="max_drawdown",
                        label_col="ticker",
                        title="Maximum drawdown by ticker",
                        higher_is_better=True,
                    ),
                    use_container_width=True,
                )