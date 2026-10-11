"""
Training loop for deep-learning sequence models.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler

from src.models.evaluation import chronological_split, evaluate_regression
from src.models.registry import ModelRegistry
from .models import get_dl_model, DL_MODEL_NAMES

logger = logging.getLogger(__name__)


def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    seq_len: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Turn a 2-D feature matrix into overlapping sequences.

    Returns
    -------
    X_seq : (n_samples, seq_len, n_features)
    y_seq : (n_samples,)
    """
    xs, ys = [], []
    for i in range(seq_len, len(X)):
        xs.append(X[i - seq_len : i])
        ys.append(y[i])
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)


class DLTrainer:
    """
    End-to-end trainer for a single deep-learning model.
    """

    def __init__(
        self,
        model_name: str,
        *,
        seq_len: int = 30,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        lr: float = 1e-3,
        batch_size: int = 64,
        epochs: int = 30,
        patience: int = 7,
        device: Optional[str] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
        random_state: int = 42,
    ):
        if model_name not in DL_MODEL_NAMES:
            raise ValueError(f"model_name must be one of {DL_MODEL_NAMES}")
        self.model_name = model_name
        self.seq_len = seq_len
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.lr = lr
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_kwargs = model_kwargs or {}
        self.random_state = random_state

        self.model: Optional[nn.Module] = None
        self.scaler: Optional[StandardScaler] = None
        self.metrics_: Dict[str, float] = {}
        self.feature_cols_: List[str] = []

        torch.manual_seed(random_state)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(random_state)

    def fit_evaluate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        gap: int = 0,
        register: bool = False,
        target_name: str = "ret_1d",
        horizon: int = 1,
    ) -> Dict[str, Any]:
        """
        Full chronological train / early-stop / test cycle.
        """
        assert len(X) == len(y)
        self.feature_cols_ = list(X.columns)
        n_features = X.shape[1]

        # Chronological split on the original rows
        split = chronological_split(
            len(X),
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            gap=gap,
        )

        X_np = X.values.astype(np.float32)
        y_np = y.values.astype(np.float32)

        # Scale – fit only on training portion
        self.scaler = StandardScaler()
        X_train_raw = self.scaler.fit_transform(X_np[split.train_idx])
        X_val_raw = self.scaler.transform(X_np[split.val_idx]) if len(split.val_idx) else np.empty((0, n_features))
        X_test_raw = self.scaler.transform(X_np[split.test_idx])

        # Build sequences (note: sequences that would cross the split boundary are dropped)
        X_train, y_train = create_sequences(X_train_raw, y_np[split.train_idx], self.seq_len)
        X_val, y_val = (
            create_sequences(X_val_raw, y_np[split.val_idx], self.seq_len)
            if len(X_val_raw) > self.seq_len
            else (np.empty((0, self.seq_len, n_features)), np.empty(0))
        )
        X_test, y_test = create_sequences(X_test_raw, y_np[split.test_idx], self.seq_len)

        if len(X_train) == 0 or len(X_test) == 0:
            raise RuntimeError("Not enough data to build sequences with the given seq_len / split")

        # DataLoaders
        train_loader = DataLoader(
            TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train)),
            batch_size=self.batch_size,
            shuffle=False,          # keep chronological order
        )
        val_loader = None
        if len(X_val):
            val_loader = DataLoader(
                TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val)),
                batch_size=self.batch_size,
                shuffle=False,
            )

        # Model
        self.model = get_dl_model(
            self.model_name,
            input_size=n_features,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            **self.model_kwargs,
        ).to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        best_val_loss = float("inf")
        best_state = None
        patience_counter = 0

        for epoch in range(1, self.epochs + 1):
            self.model.train()
            train_loss = 0.0
            for xb, yb in train_loader:
                xb, yb = xb.to(self.device), yb.to(self.device)
                optimizer.zero_grad()
                pred = self.model(xb).squeeze(-1)
                loss = criterion(pred, yb)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * len(xb)
            train_loss /= len(train_loader.dataset)

            # Validation
            val_loss = train_loss
            if val_loader is not None:
                self.model.eval()
                val_loss = 0.0
                with torch.no_grad():
                    for xb, yb in val_loader:
                        xb, yb = xb.to(self.device), yb.to(self.device)
                        pred = self.model(xb).squeeze(-1)
                        val_loss += criterion(pred, yb).item() * len(xb)
                val_loss /= len(val_loader.dataset)

            logger.debug(
                "Epoch %3d/%d  train_loss=%.6f  val_loss=%.6f",
                epoch, self.epochs, train_loss, val_loss,
            )

            if val_loss < best_val_loss - 1e-6:
                best_val_loss = val_loss
                best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.patience:
                    logger.info("Early stopping at epoch %d", epoch)
                    break

        if best_state is not None:
            self.model.load_state_dict(best_state)

        # Test evaluation
        self.model.eval()
        with torch.no_grad():
            X_test_t = torch.from_numpy(X_test).to(self.device)
            y_pred = self.model(X_test_t).squeeze(-1).cpu().numpy()

        self.metrics_ = evaluate_regression(y_test, y_pred, prefix="test_")
        self.metrics_["best_val_loss"] = float(best_val_loss)

        result = {
            "model_name": self.model_name,
            "task": "regression",
            "metrics": self.metrics_,
            "n_train_seq": len(X_train),
            "n_val_seq": len(X_val),
            "n_test_seq": len(X_test),
            "seq_len": self.seq_len,
            "feature_cols": self.feature_cols_,
        }

        if register:
            registry = ModelRegistry(model_type="dl")
            # We store the whole trainer state (model + scaler) for later inference
            artifact = {
                "model_state": self.model.state_dict(),
                "model_name": self.model_name,
                "input_size": n_features,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers,
                "dropout": self.dropout,
                "seq_len": self.seq_len,
                "scaler": self.scaler,
                "feature_cols": self.feature_cols_,
                "model_kwargs": self.model_kwargs,
            }
            model_id = registry.register(
                artifact,
                name=self.model_name,
                metrics=self.metrics_,
                params={
                    "seq_len": self.seq_len,
                    "hidden_size": self.hidden_size,
                    "num_layers": self.num_layers,
                    "dropout": self.dropout,
                    "lr": self.lr,
                    **self.model_kwargs,
                },
                feature_cols=self.feature_cols_,
                target=target_name,
                horizon=horizon,
            )
            result["model_id"] = model_id

        logger.info(
            "DLTrainer [%s] test_rmse=%.6f",
            self.model_name,
            self.metrics_.get("test_rmse", float("nan")),
        )
        return result

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions for a new feature matrix.
        The last `seq_len` rows are used to form the input sequence(s).
        """
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model has not been fitted yet")

        X_scaled = self.scaler.transform(X[self.feature_cols_].values.astype(np.float32))
        if len(X_scaled) < self.seq_len:
            raise ValueError(f"Need at least {self.seq_len} rows to form a sequence")

        # Build one sequence per possible end point
        seqs = []
        for i in range(self.seq_len, len(X_scaled) + 1):
            seqs.append(X_scaled[i - self.seq_len : i])
        X_seq = np.asarray(seqs, dtype=np.float32)

        self.model.eval()
        with torch.no_grad():
            t = torch.from_numpy(X_seq).to(self.device)
            preds = self.model(t).squeeze(-1).cpu().numpy()
        return preds