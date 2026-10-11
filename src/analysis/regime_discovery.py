"""
Unsupervised regime / behaviour clustering.

Uses the features already engineered (returns, volatility, technical)
and produces interpretable regime assignments together with
stability diagnostics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from config.constants import REGIME_LABELS

logger = logging.getLogger(__name__)


def discover_regimes(
    df: pd.DataFrame,
    feature_cols: List[str],
    *,
    n_regimes: int = 4,
    random_state: int = 42,
    min_history: int = 60,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cluster the feature space into `n_regimes` behavioural regimes.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain the columns listed in `feature_cols`.
    feature_cols : list of str
        Features used for clustering (must be causal / past-only).
    n_regimes : int
        Number of clusters (default 4 matches the four conceptual labels).
    min_history : int
        Drop rows that do not yet have enough history.

    Returns
    -------
    df_with_labels : pd.DataFrame
        Original frame + 'regime_cluster' and 'regime_label' columns.
    diagnostics : dict
        Silhouette score, cluster sizes, centroids, etc.
    """
    if len(df) < min_history:
        logger.warning("Not enough history (%d < %d) for regime discovery", len(df), min_history)
        return df.copy(), {}

    work = df[feature_cols].dropna()
    if len(work) < min_history:
        return df.copy(), {}

    scaler = StandardScaler()
    X = scaler.fit_transform(work)

    kmeans = KMeans(n_clusters=n_regimes, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X)

    # Attach back to the original index
    out = df.copy()
    out.loc[work.index, "regime_cluster"] = labels

    # Map numeric clusters to human-readable labels (by average return or vol)
    cluster_stats = _characterise_clusters(work, labels, feature_cols)
    label_map = _assign_semantic_labels(cluster_stats)
    out["regime_label"] = out["regime_cluster"].map(label_map)

    # Diagnostics
    sil = float(silhouette_score(X, labels)) if len(set(labels)) > 1 else np.nan
    diagnostics = {
        "n_regimes": n_regimes,
        "silhouette_score": sil,
        "cluster_sizes": pd.Series(labels).value_counts().to_dict(),
        "cluster_stats": cluster_stats,
        "label_map": label_map,
        "feature_cols": feature_cols,
    }
    logger.info(
        "Regime discovery finished – silhouette=%.3f, sizes=%s",
        sil,
        diagnostics["cluster_sizes"],
    )
    return out, diagnostics


def regime_summary(
    df: pd.DataFrame,
    label_col: str = "regime_label",
) -> Dict[str, Any]:
    """
    High-level summary of regime distribution and average behaviour.
    """
    if label_col not in df.columns:
        return {}

    counts = df[label_col].value_counts(dropna=False).to_dict()
    props = df[label_col].value_counts(normalize=True, dropna=False).to_dict()

    # Average 1-day return per regime (if available)
    avg_ret = {}
    if "ret_1d" in df.columns:
        avg_ret = (
            df.groupby(label_col)["ret_1d"]
            .mean()
            .replace({np.nan: None})
            .to_dict()
        )

    return {
        "counts": counts,
        "proportions": props,
        "avg_daily_return": avg_ret,
    }


def _characterise_clusters(
    features: pd.DataFrame,
    labels: np.ndarray,
    feature_cols: List[str],
) -> Dict[int, Dict[str, float]]:
    """Compute mean of each feature inside every cluster."""
    stats = {}
    for cid in sorted(set(labels)):
        mask = labels == cid
        means = features.loc[mask, feature_cols].mean().to_dict()
        stats[int(cid)] = {k: float(v) for k, v in means.items()}
    return stats


def _assign_semantic_labels(
    cluster_stats: Dict[int, Dict[str, float]],
) -> Dict[int, str]:
    """
    Heuristic mapping from numeric cluster → bull / bear / sideways / high_vol.

    Uses the presence of return and volatility related features when available.
    """
    # Prefer features that look like returns or volatility
    ret_keys = [k for k in next(iter(cluster_stats.values())) if "ret" in k.lower()]
    vol_keys = [k for k in next(iter(cluster_stats.values())) if "vol" in k.lower()]

    scores = {}
    for cid, means in cluster_stats.items():
        ret_score = np.mean([means.get(k, 0) for k in ret_keys]) if ret_keys else 0
        vol_score = np.mean([means.get(k, 0) for k in vol_keys]) if vol_keys else 0
        scores[cid] = (ret_score, vol_score)

    # Sort by return (descending) then assign
    ordered = sorted(scores.items(), key=lambda x: x[1][0], reverse=True)
    label_map = {}
    semantic = list(REGIME_LABELS.values())  # bull, bear, sideways, high_vol

    # Simple assignment: highest return → bull, lowest → bear,
    # highest vol among remaining → high_vol, last → sideways
    if len(ordered) >= 1:
        label_map[ordered[0][0]] = REGIME_LABELS["bull"]
    if len(ordered) >= 2:
        label_map[ordered[-1][0]] = REGIME_LABELS["bear"]

    remaining = [cid for cid, _ in ordered if cid not in label_map]
    if remaining:
        # highest vol among remaining → high_vol
        remaining_sorted = sorted(
            remaining, key=lambda c: scores[c][1], reverse=True
        )
        label_map[remaining_sorted[0]] = REGIME_LABELS["high_vol"]
        for cid in remaining_sorted[1:]:
            label_map[cid] = REGIME_LABELS["sideways"]

    return label_map