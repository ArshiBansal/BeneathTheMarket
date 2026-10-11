"""
Text embedding utilities.

Uses sentence-transformers when available; falls back to a simple
TF-IDF vectoriser so the component still runs in a minimal environment.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Lazy globals
_SENTENCE_MODEL = None
_TFIDF_VECTORIZER = None


def get_embedding_model(
    model_name: str = "all-MiniLM-L6-v2",
    prefer_sentence_transformers: bool = True,
):
    """
    Return a usable embedding backend.

    Tries sentence-transformers first; on ImportError or download failure
    falls back to sklearn TfidfVectorizer.
    """
    global _SENTENCE_MODEL, _TFIDF_VECTORIZER

    if prefer_sentence_transformers:
        try:
            from sentence_transformers import SentenceTransformer
            if _SENTENCE_MODEL is None:
                _SENTENCE_MODEL = SentenceTransformer(model_name)
                logger.info("Loaded sentence-transformers model: %s", model_name)
            return ("sentence_transformers", _SENTENCE_MODEL)
        except Exception as exc:
            logger.warning(
                "sentence-transformers unavailable (%s) – falling back to TF-IDF",
                exc,
            )

    # Fallback
    from sklearn.feature_extraction.text import TfidfVectorizer
    if _TFIDF_VECTORIZER is None:
        _TFIDF_VECTORIZER = TfidfVectorizer(
            max_features=512,
            ngram_range=(1, 2),
            stop_words="english",
        )
    return ("tfidf", _TFIDF_VECTORIZER)


def embed_texts(
    texts: Dict[str, str],
    *,
    model_name: str = "all-MiniLM-L6-v2",
    prefer_sentence_transformers: bool = True,
) -> Tuple[List[str], np.ndarray]:
    """
    Embed a dictionary of {id: raw_text}.

    Returns
    -------
    ids    : list of keys (same order as rows of the matrix)
    matrix : np.ndarray of shape (n_texts, embedding_dim)
    """
    # Filter empty texts
    ids = [k for k, v in texts.items() if v and v.strip()]
    raw = [texts[k] for k in ids]

    if not ids:
        logger.warning("No non-empty texts to embed")
        return [], np.zeros((0, 1))

    backend, model = get_embedding_model(
        model_name=model_name,
        prefer_sentence_transformers=prefer_sentence_transformers,
    )

    if backend == "sentence_transformers":
        matrix = model.encode(raw, show_progress_bar=False, convert_to_numpy=True)
    else:
        # TF-IDF path – fit on the provided corpus
        matrix = model.fit_transform(raw).toarray()

    logger.info(
        "Embedded %d texts with %s → shape %s",
        len(ids),
        backend,
        matrix.shape,
    )
    return ids, np.asarray(matrix, dtype=np.float32)