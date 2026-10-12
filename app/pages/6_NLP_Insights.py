"""
NLP insights – non-news company description similarity.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.nlp_service import NLPService
from app.components.filters import ticker_selector, category_selector, multi_ticker_selector
from app.components.charts import plot_correlation_heatmap
from app.components.tables import show_dataframe, metrics_cards
from app.components.status_banner import status_banner

st.set_page_config(page_title="NLP Insights", page_icon="📝", layout="wide")
st.title("NLP Insights")
st.caption(
    "Non-news text only (company / category descriptions). "
    "No news articles, no sentiment pipeline. "
    "Output is contextual analysis, not a causal explanation of prices."
)

status_banner()

nlp = NLPService()

# Coverage
st.subheader("Text coverage")
cov = nlp.coverage()
metrics_cards(nlp.summary(), columns=4)
show_dataframe(cov, height=280)

# Description viewer
st.subheader("Company description")
cat = category_selector(key="nlp_cat")
ticker = ticker_selector(category=cat, key="nlp_ticker")
if ticker:
    desc = nlp.get_description(ticker)
    if desc:
        st.write(desc)
    else:
        st.info("No description available for this ticker.")

# Similarity
st.subheader("Description similarity")
pool = cov.loc[cov["has_text"], "ticker"].tolist() if not cov.empty else []
selected = multi_ticker_selector(
    pool or None,
    default=(pool[:8] if pool else None),
    key="nlp_sim_tickers",
    max_selections=15,
)

if st.button("Compute similarity matrix", type="primary"):
    with st.spinner("Embedding texts (first run may download a small model)..."):
        sim = nlp.build_similarity(tickers=selected or None)
    if sim.empty:
        st.warning("Could not build similarity matrix (insufficient text).")
    else:
        st.plotly_chart(
            plot_correlation_heatmap(sim, title="Description cosine similarity"),
            use_container_width=True,
        )
        if ticker and ticker in sim.index:
            st.write(f"Most similar to **{ticker}**:")
            neighbours = nlp.most_similar(ticker, top_n=5)
            show_dataframe(
                pd.DataFrame(neighbours, columns=["neighbour", "similarity"])
            )

with st.expander("Category descriptions (static, project-owned)"):
    cats = nlp.get_category_descriptions()
    for name, text in cats.items():
        st.markdown(f"**{name}**")
        st.write(text)