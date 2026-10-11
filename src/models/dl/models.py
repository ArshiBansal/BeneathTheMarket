"""
Deep-learning architectures for sequential market data.

Supported models (>3 required)
------------------------------
lstm, gru, tcn, transformer
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

DL_MODEL_NAMES: List[str] = [
    "lstm",
    "gru",
    "tcn",
    "transformer",
]


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class LSTMModel(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size)
        out, _ = self.lstm(x)
        last = out[:, -1, :]          # (batch, hidden)
        return self.head(last)


class GRUModel(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1,
    ):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.gru(x)
        last = out[:, -1, :]
        return self.head(last)


class TemporalBlock(nn.Module):
    """Single residual TCN block."""

    def __init__(self, in_ch: int, out_ch: int, kernel_size: int, dilation: int, dropout: float):
        super().__init__()
        padding = (kernel_size - 1) * dilation
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size, padding=padding, dilation=dilation)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size, padding=padding, dilation=dilation)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.downsample = nn.Conv1d(in_ch, out_ch, 1) if in_ch != out_ch else None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, channels, seq_len)
        residual = x if self.downsample is None else self.downsample(x)
        out = self.conv1(x)[:, :, :x.size(2)]          # causal crop
        out = self.dropout(self.relu(out))
        out = self.conv2(out)[:, :, :x.size(2)]
        out = self.dropout(self.relu(out))
        return self.relu(out + residual)


class TCNModel(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_levels: int = 3,
        kernel_size: int = 3,
        dropout: float = 0.2,
        output_size: int = 1,
    ):
        super().__init__()
        layers = []
        for i in range(num_levels):
            in_ch = input_size if i == 0 else hidden_size
            dilation = 2 ** i
            layers.append(TemporalBlock(in_ch, hidden_size, kernel_size, dilation, dropout))
        self.network = nn.Sequential(*layers)
        self.head = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size) → (batch, input_size, seq_len)
        x = x.transpose(1, 2)
        out = self.network(x)
        last = out[:, :, -1]          # (batch, hidden)
        return self.head(last)


class TimeSeriesTransformer(nn.Module):
    def __init__(
        self,
        input_size: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
        output_size: int = 1,
        max_seq_len: int = 128,
    ):
        super().__init__()
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_encoding = nn.Parameter(torch.zeros(1, max_seq_len, d_model))
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size)
        seq_len = x.size(1)
        h = self.input_proj(x) + self.pos_encoding[:, :seq_len, :]
        h = self.encoder(h)
        last = h[:, -1, :]
        return self.head(last)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_dl_model(
    name: str,
    input_size: int,
    *,
    output_size: int = 1,
    hidden_size: int = 64,
    num_layers: int = 2,
    dropout: float = 0.2,
    **kwargs,
) -> nn.Module:
    """
    Instantiate a deep-learning model by name.
    """
    name = name.lower().strip()
    if name not in DL_MODEL_NAMES:
        raise ValueError(f"Unknown DL model '{name}'. Choose from {DL_MODEL_NAMES}")

    if name == "lstm":
        return LSTMModel(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            output_size=output_size,
            **kwargs,
        )
    if name == "gru":
        return GRUModel(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            output_size=output_size,
            **kwargs,
        )
    if name == "tcn":
        return TCNModel(
            input_size=input_size,
            hidden_size=hidden_size,
            num_levels=kwargs.pop("num_levels", 3),
            kernel_size=kwargs.pop("kernel_size", 3),
            dropout=dropout,
            output_size=output_size,
            **kwargs,
        )
    if name == "transformer":
        return TimeSeriesTransformer(
            input_size=input_size,
            d_model=hidden_size,
            nhead=kwargs.pop("nhead", 4),
            num_layers=num_layers,
            dim_feedforward=kwargs.pop("dim_feedforward", 128),
            dropout=dropout,
            output_size=output_size,
            max_seq_len=kwargs.pop("max_seq_len", 128),
            **kwargs,
        )

    raise RuntimeError(f"Unhandled DL model: {name}")