"""
Post-processing of ForecastResult objects before storage or display.

Responsibilities
----------------
- Convert a ForecastResult into the exact document shape expected by
  the predictions collection.
- Attach standardised uncertainty / limitation notes so that the UI
  never presents a point forecast as a guarantee.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .predictor import ForecastResult

logger = logging.getLogger(__name__)

# Standard disclaimer text (kept short for UI banners)
DEFAULT_UNCERTAINTY_NOTES = [
    "Forecasts are uncertain estimates and may fail during unexpected events or regime shifts.",
    "Historical performance does not guarantee future performance.",
    "This output is for academic analysis only and is not personalised investment advice.",
    "Point forecasts do not incorporate transaction costs, slippage or liquidity constraints.",
]


def format_forecast_for_storage(
    result: ForecastResult,
    *,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Turn a ForecastResult into a clean dictionary ready for
    `src.db.predictions.save_prediction`.

    The returned document contains every field required by the
    project data model plus any caller-supplied extras.
    """
    doc = result.to_dict()

    # Guarantee the keys expected by the predictions collection
    doc.setdefault("ticker", result.ticker.upper())
    doc.setdefault("horizon", int(result.horizon))
    doc.setdefault("predicted_value", float(result.predicted_value))
    doc.setdefault("model_id", result.model_id)
    doc.setdefault("model_version", result.model_id)  # alias used in some queries
    doc.setdefault("generated_at", result.generated_at)
    doc.setdefault("input_cutoff", result.input_cutoff)

    if extra_fields:
        doc.update(extra_fields)

    return doc


def attach_uncertainty_notes(
    result: ForecastResult,
    *,
    custom_notes: Optional[List[str]] = None,
    include_default: bool = True,
) -> ForecastResult:
    """
    Attach human-readable uncertainty notes to the metadata of a
    ForecastResult (in-place and returned for convenience).
    """
    notes: List[str] = []
    if include_default:
        notes.extend(DEFAULT_UNCERTAINTY_NOTES)
    if custom_notes:
        notes.extend(custom_notes)

    # Avoid duplicates while preserving order
    seen = set()
    unique_notes = []
    for n in notes:
        if n not in seen:
            seen.add(n)
            unique_notes.append(n)

    result.metadata["uncertainty_notes"] = unique_notes
    result.metadata["notes_attached_at"] = datetime.utcnow().isoformat()
    return result


def batch_format_for_storage(
    results: List[ForecastResult],
    *,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Apply `format_forecast_for_storage` to a list of results.
    """
    return [
        format_forecast_for_storage(r, extra_fields=extra_fields) for r in results
    ]


def summarise_forecast_batch(
    results: List[ForecastResult],
) -> Dict[str, Any]:
    """
    Produce a lightweight summary useful for logs or a Streamlit status card.
    """
    if not results:
        return {"n_forecasts": 0}

    tickers = sorted({r.ticker for r in results})
    horizons = sorted({r.horizon for r in results})
    models = sorted({r.model_name for r in results})

    return {
        "n_forecasts": len(results),
        "tickers": tickers,
        "horizons": horizons,
        "models": models,
        "generated_at_range": {
            "min": min(r.generated_at for r in results).isoformat(),
            "max": max(r.generated_at for r in results).isoformat(),
        },
    }