"""
Plotly / Altair-style chart helpers for Streamlit pages.
All functions return a figure object that the caller can st.plotly_chart().
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plot_price(
    df: pd.DataFrame,
    *,
    price_col: str = "close",
    title: str = "Price",
    height: int = 400,
) -> go.Figure:
    """Single-series close (or other) price chart."""
    fig = go.Figure()
    if df is None or df.empty or price_col not in df.columns:
        fig.update_layout(title=title + " (no data)", height=height)
        return fig

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[price_col],
            mode="lines",
            name=price_col,
            line=dict(width=1.5, color="#1f77b4"),
        )
    )
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis_title="Date",
        yaxis_title=price_col.capitalize(),
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def plot_returns(
    df: pd.DataFrame,
    *,
    return_col: str = "ret_1d",
    title: str = "Daily returns",
    height: int = 280,
) -> go.Figure:
    """Bar / line chart of returns."""
    fig = go.Figure()
    if df is None or df.empty:
        fig.update_layout(title=title + " (no data)", height=height)
        return fig

    series = df[return_col] if return_col in df.columns else df.iloc[:, 0].pct_change()
    colors = np.where(series >= 0, "#2ca02c", "#d62728")
    fig.add_trace(
        go.Bar(x=series.index, y=series.values, marker_color=colors, name=return_col)
    )
    fig.add_hline(y=0, line_width=0.8, line_color="black")
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        template="plotly_white",
        showlegend=False,
    )
    return fig


def plot_underwater(
    prices: pd.Series,
    *,
    title: str = "Underwater curve (drawdown)",
    height: int = 280,
) -> go.Figure:
    """Drawdown from expanding peak."""
    fig = go.Figure()
    if prices is None or prices.empty:
        fig.update_layout(title=title + " (no data)", height=height)
        return fig

    dd = prices / prices.cummax() - 1.0
    fig.add_trace(
        go.Scatter(
            x=dd.index,
            y=dd.values,
            fill="tozeroy",
            mode="lines",
            line=dict(width=1, color="#d62728"),
            name="drawdown",
        )
    )
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        yaxis_tickformat=".0%",
        template="plotly_white",
        showlegend=False,
    )
    return fig


def plot_correlation_heatmap(
    corr: pd.DataFrame,
    *,
    title: str = "Return correlation",
    height: int = 500,
) -> go.Figure:
    """Correlation heatmap."""
    if corr is None or corr.empty:
        fig = go.Figure()
        fig.update_layout(title=title + " (no data)", height=height)
        return fig

    fig = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        aspect="auto",
        title=title,
    )
    fig.update_layout(height=height, margin=dict(l=60, r=20, t=50, b=60))
    return fig


def plot_bar_ranking(
    df: pd.DataFrame,
    value_col: str,
    label_col: str = "model",
    *,
    title: str = "Ranking",
    higher_is_better: bool = False,
    height: int = 400,
    color_col: Optional[str] = None,
) -> go.Figure:
    """Horizontal or vertical bar ranking (e.g. model RMSE)."""
    if df is None or df.empty or value_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(title=title + " (no data)", height=height)
        return fig

    plot_df = df.sort_values(value_col, ascending=higher_is_better).copy()
    fig = px.bar(
        plot_df,
        x=label_col if label_col in plot_df.columns else plot_df.index,
        y=value_col,
        color=color_col if color_col and color_col in plot_df.columns else None,
        title=title,
    )
    fig.update_layout(
        height=height,
        margin=dict(l=40, r=20, t=50, b=80),
        template="plotly_white",
        xaxis_tickangle=-40,
    )
    return fig


def plot_ohlcv_candles(
    df: pd.DataFrame,
    *,
    title: str = "OHLCV",
    height: int = 450,
) -> go.Figure:
    """Candlestick chart when OHLC columns are present."""
    required = {"open", "high", "low", "close"}
    fig = go.Figure()
    if df is None or df.empty or not required.issubset(df.columns):
        fig.update_layout(title=title + " (no data)", height=height)
        return fig

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03
    )
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )
    if "volume" in df.columns:
        fig.add_trace(
            go.Bar(x=df.index, y=df["volume"], name="Volume", marker_color="#9ecae1"),
            row=2,
            col=1,
        )
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )
    return fig