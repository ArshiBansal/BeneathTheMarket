"""
Cross-company comparison – relative performance, risk and correlations.
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
from app.components.filters import multi_ticker_selector, category_selector, date_range_selector
from app.components.charts import plot_correlation_heatmap, plot_bar_ranking, plot_price
from app.components.tables import style_dataframe, show_dataframe
from app.components.status_banner import status_banner
from src.analysis.comparison import compare_tickers, category_summary
from src.analysis.correlation import correlation_matrix

st.set_page_config(page_title="Cross-Company Comparison", page_icon="🔄", layout="wide")
st.title("Cross-Company Comparison")
st.caption("Compare returns, volatility and co-movement across selected tickers.")

status_banner()

cat = category_selector(key="cmp_category")
pool = DataService.list_tickers(category=cat)
tickers = multi_ticker_selector(pool, default=pool[:6], key="cmp_tickers")
start, end = date_range_selector(default_days=365, key="cmp_dates")

if len(tickers) < 2:
    st.info("Select at least two tickers.")
    st.stop()

# Load close panel
panel = DataService.load_close_panel(
    tickers,
    start=pd.Timestamp(start) if start else None,
    end=pd.Timestamp(end) if end else None,
)
if panel.empty:
    st.warning("No overlapping data for the selected tickers.")
    st.stop()

# Normalised price chart
normed = panel / panel.iloc[0]
st.subheader("Normalised price (base = 1)")
st.plotly_chart(
    plot_price(normed, price_col=normed.columns[0], title="Normalised closes"),
    use_container_width=True,
)
# multi-line via plotly express-style
import plotly.express as px
fig = px.line(normed, title="Normalised price comparison")
fig.update_layout(height=400, template="plotly_white", legend_title="Ticker")
st.plotly_chart(fig, use_container_width=True)

# Comparison table
price_dict = {t: panel[t].dropna() for t in panel.columns}
comp = compare_tickers(price_dict, windows=[21, 63, 252])
st.subheader("Performance & risk table")
show_dataframe(comp.round(4), height=400)

if "category" in comp.columns:
    st.subheader("Category aggregates (63-day total return)")
    show_dataframe(category_summary(comp, metric="total_return_63d").round(4))

# Correlation
st.subheader("Return correlation")
corr = correlation_matrix(price_dict)
st.plotly_chart(
    plot_correlation_heatmap(corr, title="Pairwise return correlation"),
    use_container_width=True,
)