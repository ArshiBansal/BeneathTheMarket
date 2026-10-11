"""
Lightweight model registry – tracks metadata and artifact paths.

Artifacts themselves live under data/models/{ml,dl}/; this module only
stores JSON-serialisable metadata in MongoDB (model_evaluations collection)
and on disk.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

from config import settings
from src.db.model_evaluations import save_model_evaluation, get_model_evaluations

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Register, load and query trained models.

    Parameters
    ----------
    model_type : str
        'ml' or 'dl' – determines the sub-folder under data/models/.
    """

    def __init__(self, model_type: str = "ml"):
        if model_type not in ("ml", "dl"):
            raise ValueError("model_type must be 'ml' or 'dl'")
        self.model_type = model_type
        self.root = settings.ML_MODELS_DIR if model_type == "ml" else settings.DL_MODELS_DIR
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(
        self,
        model: Any,
        *,
        name: str,
        metrics: Dict[str, float],
        params: Optional[Dict[str, Any]] = None,
        feature_cols: Optional[List[str]] = None,
        target: str = "ret_1d",
        horizon: int = 1,
        train_end: Optional[str] = None,
        test_start: Optional[str] = None,
        test_end: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Persist a fitted model + metadata.

        Returns the unique model_id.
        """
        model_id = f"{name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        artifact_path = self.root / f"{model_id}.joblib"

        # Save binary artifact
        joblib.dump(model, artifact_path)
        logger.info("Saved model artifact → %s", artifact_path)

        meta = {
            "model_id": model_id,
            "model_type": self.model_type,
            "name": name,
            "artifact_path": str(artifact_path),
            "metrics": metrics,
            "params": params or {},
            "feature_cols": feature_cols or [],
            "target": target,
            "horizon": horizon,
            "train_end": train_end,
            "test_start": test_start,
            "test_end": test_end,
            "created_at": datetime.utcnow().isoformat(),
        }
        if extra:
            meta.update(extra)

        # Also write a small JSON sidecar for quick inspection
        sidecar = artifact_path.with_suffix(".json")
        with open(sidecar, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

        # Persist evaluation record in MongoDB
        save_model_evaluation(meta)
        logger.info("Registered model_id=%s  (RMSE/metric keys=%s)", model_id, list(metrics.keys()))
        return model_id

    # Loading
    def load(self, model_id: str) -> Any:
        """Load a previously registered model by its id."""
        # Prefer the path stored in MongoDB; fall back to convention
        records = get_model_evaluations(model_id=model_id, limit=1)
        if records:
            path = Path(records[0]["artifact_path"])
        else:
            path = self.root / f"{model_id}.joblib"

        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        model = joblib.load(path)
        logger.debug("Loaded model %s from %s", model_id, path)
        return model

    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Return the metadata document for a model_id (or None)."""
        records = get_model_evaluations(model_id=model_id, limit=1)
        return records[0] if records else None

    def list_models(
        self,
        name: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List registered models, newest first."""
        records = get_model_evaluations(model_type=self.model_type, limit=limit)
        if name:
            records = [r for r in records if r.get("name") == name]
        return records

    def best_model(
        self,
        metric: str = "rmse",
        higher_is_better: bool = False,
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the metadata of the best model according to `metric`.
        """
        records = self.list_models(name=name, limit=200)
        if not records:
            return None

        def key_fn(r):
            return r.get("metrics", {}).get(metric, float("inf") if not higher_is_better else float("-inf"))

        records = [r for r in records if metric in r.get("metrics", {})]
        if not records:
            return None

        records.sort(key=key_fn, reverse=higher_is_better)
        return records[0]