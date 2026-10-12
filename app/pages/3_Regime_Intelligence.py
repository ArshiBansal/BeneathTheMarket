"""
Regime intelligence – rule-based and discovered regime summaries.
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
from app.components.charts import plot_price
from app.components.tables import show_dataframe, metrics_cards
from app.components.status_banner import status_banner
from src.features.returns import add_returns
from src.features.volatility import add_volatility
from src.features.regime_labels import build_regime_labels, regime_transition_matrix

st.set_page_config(page_title="Regime Intelligence", page_icon="📊", layout="wide")
st.title("Regime Intelligence")
st.caption(
    "Operational regime labels (trend / volatility based). "
    "These are analytical classifications, not causal explanations."
)

status_banner()

cat = category_selector(key="rg_category")
ticker = ticker_selector(category=cat, key="rg_ticker")
if not ticker:
    st.stop()

df = DataService.load_ohlcv(ticker)
if df.empty:
    st.warning(f"No data for {ticker}.")
    st.stop()

df = add_returns(df)
df = add_volatility(df)
df = build_regime_labels(df)

# Distribution
st.subheader(f"Regime distribution – {ticker}")
counts = df["regime"].value_counts(dropna=False)
metrics_cards(counts.to_dict(), columns=4)

# Colour price by regime
st.subheader("Price coloured by regime")
import plotly.express as px
plot_df = df.reset_index()[["timestamp", "close", "regime"]].dropna()
fig = px.scatter(
    plot_df,
    x="timestamp",
    y="close",
    color="regime",
    title=f"{ticker} – regimes",
    height=420,
)
fig.update_traces(marker=dict(size=4))
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# Transition matrix
st.subheader("Regime transition counts")
trans = regime_transition_matrix(df["regime"].dropna())
show_dataframe(trans)

# Optional discovered regimes from notebook 04
panel_path = settings.PROCESSED_DATA_DIR / "feature_panel_with_regimes.parquet"
if panel_path.exists():
    with st.expander("Discovered regimes (from research pipeline)"):
        panel = pd.read_parquet(panel_path)
        sub = panel[panel["ticker"] == ticker]
        if "regime_discovered" in sub.columns and not sub.empty:
            st.write(sub["regime_discovered"].value_counts())
        else:
            st.info("No discovered-regime column for this ticker.")
else:
    st.caption("Run notebook 04 to attach unsupervised regime labels.")