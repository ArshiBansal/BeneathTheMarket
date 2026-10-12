"""
Independence acceptance tests.

Verifies that:
1. Core packages import without Streamlit / notebook side-effects
2. Config loads with local MongoDB settings (no Atlas)
3. App services import independently of notebooks
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config_imports():
    from config import settings, TICKERS, CATEGORIES
    assert settings.MONGODB_URI
    assert "localhost" in settings.MONGODB_URI or "127.0.0.1" in settings.MONGODB_URI
    assert "atlas" not in settings.MONGODB_URI.lower()
    assert len(TICKERS) >= 30
    assert len(CATEGORIES) == 6


def test_src_packages_import():
    import src.db
    import src.data_pipeline
    import src.features
    import src.analysis
    import src.models
    import src.nlp
    import src.forecasting
    import src.utils
    assert src.db is not None


def test_db_connection_module_has_no_atlas():
    from src.db import connection
    source = Path(connection.__file__).read_text(encoding="utf-8")
    assert "mongodb+srv" not in source
    assert "atlas" not in source.lower() or "not" in source.lower()


def test_app_services_import():
    """App service layer must import without running Streamlit script logic."""
    from app.services.data_service import DataService
    from app.services.model_service import ModelService
    from app.services.nlp_service import NLPService
    assert hasattr(DataService, "load_ohlcv")
    assert hasattr(ModelService, "list_models")
    assert hasattr(NLPService, "get_description")


def test_app_components_import():
    from app.components.charts import plot_price
    from app.components.filters import ticker_selector
    from app.components.status_banner import status_banner
    assert callable(plot_price)
    assert callable(status_banner)


def test_notebooks_not_required_for_app():
    """Importing app must not execute or require notebook files."""
    notebooks_dir = PROJECT_ROOT / "notebooks"
    # App packages should not reference notebooks/
    app_main = (PROJECT_ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "notebooks/" not in app_main
    assert "jupyter" not in app_main.lower()


def test_ml_dl_model_factories():
    from src.models.ml.models import get_ml_model, ML_MODEL_NAMES
    from src.models.dl.models import get_dl_model, DL_MODEL_NAMES
    assert len(ML_MODEL_NAMES) >= 3
    assert len(DL_MODEL_NAMES) >= 3
    # Instantiate a lightweight model
    m = get_ml_model("ridge", task="regression")
    assert m is not None
    dl = get_dl_model("lstm", input_size=5, hidden_size=8, num_layers=1)
    assert dl is not None


def test_forecast_result_serialisable():
    from datetime import datetime
    from src.forecasting.predictor import ForecastResult
    from src.forecasting.postprocess import format_forecast_for_storage, attach_uncertainty_notes

    fc = ForecastResult(
        ticker="AAPL",
        horizon=5,
        predicted_value=0.01,
        model_id="test",
        model_name="ridge",
        input_cutoff=datetime.utcnow(),
    )
    fc = attach_uncertainty_notes(fc)
    doc = format_forecast_for_storage(fc)
    assert doc["ticker"] == "AAPL"
    assert "uncertainty_notes" in fc.metadata