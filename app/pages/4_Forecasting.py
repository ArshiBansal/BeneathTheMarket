"""
Forecasting – view stored predictions and model leaderboard.
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
from app.services.model_service import ModelService
from app.components.filters import ticker_selector, category_selector, horizon_selector
from app.components.charts import plot_bar_ranking
from app.components.tables import show_dataframe, metrics_cards
from app.components.status_banner import status_banner

st.set_page_config(page_title="Forecasting", page_icon="🔮", layout="wide")
st.title("Forecasting")
st.caption(
    "Stored forecasts and model rankings. "
    "Forecasts are uncertain estimates — not investment advice."
)

status_banner()

ms = ModelService(model_type="ml")

# Leaderboard
st.subheader("Model leaderboard (test set)")
lb = ModelService.load_leaderboard(limit=20)
if lb.empty:
    st.info("No leaderboard yet. Run notebooks 05–08 to populate results.")
else:
    st.plotly_chart(
        plot_bar_ranking(
            lb,
            value_col="test_rmse",
            label_col="model",
            color_col="family" if "family" in lb.columns else None,
            title="Test RMSE (lower is better)",
        ),
        use_container_width=True,
    )
    show_dataframe(lb, height=320)

# Stored predictions
st.subheader("Stored predictions")
cat = category_selector(key="fc_category")
ticker = ticker_selector(category=cat, key="fc_ticker")
horizon = horizon_selector(key="fc_horizon")

preds = ms.list_predictions(ticker=ticker or None, horizon=horizon, limit=30)
if not preds:
    st.info(
        "No stored predictions for this selection. "
        "Generate forecasts via the research notebooks or training scripts."
    )
else:
    pred_df = pd.DataFrame(preds)
    cols = [
        c for c in [
            "ticker", "horizon", "predicted_value", "predicted_return",
            "model_name", "model_id", "input_cutoff", "generated_at",
        ]
        if c in pred_df.columns
    ]
    show_dataframe(pred_df[cols], height=350)

    latest = preds[0]
    metrics_cards(
        {
            "Ticker": latest.get("ticker"),
            "Horizon": latest.get("horizon"),
            "Predicted value": latest.get("predicted_value"),
            "Model": latest.get("model_name") or latest.get("model_id"),
        },
        columns=4,
        title="Most recent stored forecast",
    )
    notes = (latest.get("metadata") or {}).get("uncertainty_notes") or []
    if notes:
        with st.expander("Uncertainty notes"):
            for n in notes:
                st.write(f"- {n}")