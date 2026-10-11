# src/__init__.py
"""
Technology & Fintech Market Intelligence and Regime Analyzer
===========================================================

Core source package containing:

- db/               Local MongoDB (PyMongo) access layer
- data_pipeline/    yfinance retrieval, normalization, ingestion & refresh
- features/         Feature engineering (returns, volatility, regimes, etc.)
- analysis/         EDA, correlations, drawdowns, regime discovery
- models/           ML & DL trainers, evaluation, model registry
- nlp/              Non-news text analysis component
- forecasting/      Prediction helpers and post-processing
- utils/            Logging, time utilities, I/O helpers

The Jupyter notebooks and the Streamlit application both import from
this package and connect independently to the same local MongoDB
instance.  No MongoDB Atlas dependency exists.
"""

__version__ = "0.1.0"
__author__ = "Technology & Fintech Market Intelligence Project"

# Optional convenience re-exports (keeps import paths short)
# Users can still do: from src.db.connection import get_db
# or the shorter forms below once the sub-packages are fully implemented.

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("technology-fintech-market-intelligence")
except PackageNotFoundError:
    # package is not installed; keep the hardcoded version
    pass

__all__ = [
    "__version__",
]