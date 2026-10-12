"""
Reusable Streamlit UI components.

Public API
----------
from app.components import (
    plot_price,
    plot_returns,
    plot_underwater,
    plot_correlation_heatmap,
    style_dataframe,
    ticker_selector,
    category_selector,
    date_range_selector,
    status_banner,
)
"""

from .charts import (
    plot_price,
    plot_returns,
    plot_underwater,
    plot_correlation_heatmap,
    plot_bar_ranking,
)
from .tables import style_dataframe, metrics_cards
from .filters import ticker_selector, category_selector, date_range_selector, horizon_selector
from .status_banner import status_banner

__all__ = [
    "plot_price",
    "plot_returns",
    "plot_underwater",
    "plot_correlation_heatmap",
    "plot_bar_ranking",
    "style_dataframe",
    "metrics_cards",
    "ticker_selector",
    "category_selector",
    "date_range_selector",
    "horizon_selector",
    "status_banner",
]