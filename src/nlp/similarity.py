"""
Similarity and matching utilities for the non-news NLP component.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


def compute_similarity_matrix(
    ids: List[str],
    embeddings: np.ndarray,
) -> pd.DataFrame:
    """
    Pairwise cosine similarity matrix.

    Returns a DataFrame indexed and columned by the supplied ids.
    """
    if len(ids) == 0 or embeddings.size == 0:
        return pd.DataFrame()

    sim = cosine_similarity(embeddings)
    # Numerical safety
    np.fill_diagonal(sim, 1.0)
    return pd.DataFrame(sim, index=ids, columns=ids)


def most_similar_companies(
    sim_matrix: pd.DataFrame,
    ticker: str,
    top_n: int = 5,
) -> List[Tuple[str, float]]:
    """
    Return the top-N most similar tickers to the query ticker
    (excluding itself).
    """
    ticker = ticker.upper()
    if ticker not in sim_matrix.index:
        return []

    scores = sim_matrix.loc[ticker].drop(ticker, errors="ignore")
    ranked = scores.sort_values(ascending=False).head(top_n)
    return list(zip(ranked.index.tolist(), ranked.values.tolist()))


def match_text_to_regimes(
    company_ids: List[str],
    company_embeddings: np.ndarray,
    regime_labels: Dict[str, str],
    *,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Simple matching of company text embeddings to regime behaviour groups.

    Parameters
    ----------
    company_ids : list of ticker strings (order matches embeddings rows)
    company_embeddings : (n_companies, dim)
    regime_labels : {ticker: regime_label} obtained from the regime module
    top_k : number of nearest companies to consider when characterising
            each regime

    Returns
    -------
    dict with:
        - regime_centroids (optional)
        - regime_to_companies : {regime: [(ticker, score), ...]}
        - company_to_nearest_regime : {ticker: regime}
    """
    if not company_ids or company_embeddings.size == 0:
        return {}

    # Build regime → list of embedding indices
    regime_to_indices: Dict[str, List[int]] = {}
    for i, tid in enumerate(company_ids):
        lab = regime_labels.get(tid)
        if lab is None:
            continue
        regime_to_indices.setdefault(lab, []).append(i)

    # Centroid per regime
    centroids = {}
    for lab, idxs in regime_to_indices.items():
        centroids[lab] = company_embeddings[idxs].mean(axis=0)

    if not centroids:
        return {"regime_to_companies": {}, "company_to_nearest_regime": {}}

    # Distance of every company to every regime centroid
    centroid_matrix = np.stack(list(centroids.values()))
    regime_names = list(centroids.keys())
    sims = cosine_similarity(company_embeddings, centroid_matrix)

    company_to_nearest = {}
    regime_to_companies: Dict[str, List[Tuple[str, float]]] = {r: [] for r in regime_names}

    for i, tid in enumerate(company_ids):
        best_j = int(np.argmax(sims[i]))
        best_regime = regime_names[best_j]
        score = float(sims[i, best_j])
        company_to_nearest[tid] = best_regime
        regime_to_companies[best_regime].append((tid, score))

    # Keep only top_k per regime
    for lab in regime_to_companies:
        regime_to_companies[lab] = sorted(
            regime_to_companies[lab], key=lambda x: x[1], reverse=True
        )[:top_k]

    result = {
        "regime_to_companies": regime_to_companies,
        "company_to_nearest_regime": company_to_nearest,
        "regime_names": regime_names,
    }
    logger.info(
        "Matched %d companies to %d regimes",
        len(company_to_nearest),
        len(regime_names),
    )
    return result


def keyword_overlap_score(
    tokens_a: List[str],
    tokens_b: List[str],
) -> float:
    """
    Simple Jaccard overlap – useful as a transparent baseline
    alongside dense embeddings.
    """
    set_a, set_b = set(tokens_a), set(tokens_b)
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0