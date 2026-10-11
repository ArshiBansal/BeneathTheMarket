"""
Feature-engineering package.

All feature functions operate on pandas DataFrames that contain at least
the columns: open, high, low, close, volume and a DatetimeIndex named
'timestamp' (or a column called 'timestamp').

Public API
----------
from src.features import (
    add_returns,
    add_volatility,
    add_technical,
    add_cross_company_features,
    build_regime_labels,
    build_feature_matrix,
)
"""

from .returns import add_returns
from .volatility import add_volatility
from .technical import add_technical
from .cross_company import add_cross_company_features
from .regime_labels import build_regime_labels

__all__ = [
    "add_returns",
    "add_volatility",
    "add_technical",
    "add_cross_company_features",
    "build_regime_labels",
    "build_feature_matrix",
]


def build_feature_matrix(
    df,
    *,
    include_returns: bool = True,
    include_volatility: bool = True,
    include_technical: bool = True,
    dropna: bool = True,
):
    """
    Convenience wrapper that applies the standard feature set
    in a leakage-safe order (past-only rolling windows).
    """
    out = df.copy()
    if include_returns:
        out = add_returns(out)
    if include_volatility:
        out = add_volatility(out)
    if include_technical:
        out = add_technical(out)
    if dropna:
        out = out.dropna()
    return out