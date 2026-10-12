"""
Batch training script for classical ML models.

Loads the feature panel, trains the configured ML models on the
chronological train split, evaluates on the test split, and registers
artefacts via ModelRegistry.

Usage
-----
    python scripts/train_and_register_models.py
    python scripts/train_and_register_models.py --models ridge xgboost lightgbm
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from config.constants import ML_MODELS, RANDOM_SEED
from src.utils import setup_logging, get_logger, utc_now, ensure_dir, save_json
from src.db.connection import get_client, close_client
from src.db.collections import ensure_indexes
from src.db.analysis_results import save_analysis_result
from src.models.ml import get_ml_model, ML_MODEL_NAMES
from src.models.evaluation import evaluate_regression
from src.models.registry import ModelRegistry

setup_logging(level="INFO")
logger = get_logger(__name__)
np.random.seed(RANDOM_SEED)


def main(models: list[str] | None = None) -> None:
    processed_dir = ensure_dir(settings.PROCESSED_DATA_DIR)
    panel_path = processed_dir / "feature_panel_with_regimes.parquet"
    if not panel_path.exists():
        panel_path = processed_dir / "feature_panel.parquet"
    if not panel_path.exists():
        raise FileNotFoundError(
            f"No feature panel found at {panel_path}. Run notebook 03 first."
        )

    meta_path = processed_dir / "feature_metadata.json"
    with open(meta_path, "r", encoding="utf-8") as f:
        feature_meta = json.load(f)

    panel = pd.read_parquet(panel_path)
    panel = panel.loc[:, ~panel.columns.duplicated()].copy()

    horizon = feature_meta.get("horizon", 5)
    target_ret = f"target_ret_{horizon}d"
    feature_cols = [
        c for c in feature_meta["feature_cols"]
        if c in panel.columns and pd.api.types.is_numeric_dtype(panel[c])
    ]
    feature_cols = [c for c in feature_cols if c not in ("regime_cluster", "regime_id")]

    work = panel.dropna(subset=[target_ret] + feature_cols)
    X_train = work.loc[work["split"] == "train", feature_cols]
    y_train = work.loc[work["split"] == "train", target_ret]
    X_test = work.loc[work["split"] == "test", feature_cols]
    y_test = work.loc[work["split"] == "test", target_ret]

    logger.info(
        "Train=%d  Test=%d  Features=%d  Target=%s",
        len(X_train), len(X_test), len(feature_cols), target_ret,
    )

    to_run = models or list(ML_MODEL_NAMES)
    to_run = [m for m in to_run if m in ML_MODEL_NAMES]
    if not to_run:
        raise ValueError(f"No valid models. Choose from {ML_MODEL_NAMES}")

    get_client()
    ensure_indexes()
    registry = ModelRegistry(model_type="ml")
    results = {}

    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X_train)
    X_te = scaler.transform(X_test)

    for name in to_run:
        logger.info("Training %s ...", name)
        try:
            model = get_ml_model(name, task="regression", random_state=RANDOM_SEED)
            model.fit(X_tr, y_train.values)
            y_pred = model.predict(X_te)
            metrics = evaluate_regression(y_test.values, y_pred, prefix="test_")

            model_id = registry.register(
                model,
                name=name,
                metrics=metrics,
                params={"task": "regression", "horizon": horizon},
                feature_cols=feature_cols,
                target=target_ret,
                horizon=horizon,
                train_end=feature_meta.get("train_end"),
                test_start=str(X_test.index.min().date()) if len(X_test) else None,
                test_end=str(X_test.index.max().date()) if len(X_test) else None,
            )
            metrics["model_id"] = model_id
            results[name] = metrics
            logger.info(
                "  %s  RMSE=%.5f  DirAcc=%.3f  id=%s",
                name,
                metrics["test_rmse"],
                metrics["test_directional_accuracy"],
                model_id,
            )
        except Exception as exc:
            logger.warning("Model %s failed: %s", name, exc)
            results[name] = {"error": str(exc)}

    out_path = processed_dir / "script_ml_results.json"
    save_json(
        {
            "run_at": utc_now().isoformat(),
            "horizon": horizon,
            "models": results,
        },
        out_path,
    )
    logger.info("Results saved → %s", out_path)

    save_analysis_result({
        "analysis_type": "script_ml_training",
        "as_of": utc_now().isoformat(),
        "payload": {
            "n_models": len([v for v in results.values() if "error" not in v]),
            "horizon": horizon,
        },
    })
    close_client()
    logger.info("train_and_register_models.py finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch-train classical ML models")
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help=f"Subset of {ML_MODEL_NAMES}",
    )
    args = parser.parse_args()
    main(models=args.models)