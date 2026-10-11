"""
Lightweight text cleaning and tokenisation for company / sector descriptions.

No news-specific pipelines; only generic English cleaning suitable for
short business text.
"""

from __future__ import annotations

import logging
import re
import string
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Minimal stop-word list (avoid heavy NLTK download at import time)
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "it", "its", "as", "into", "over", "after",
    "before", "between", "under", "above", "such", "no", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "also",
}


def tokenize_and_clean(
    text: str,
    *,
    lower: bool = True,
    remove_punctuation: bool = True,
    remove_stopwords: bool = True,
    min_token_len: int = 2,
) -> List[str]:
    """
    Convert a raw description into a list of clean tokens.
    """
    if not text or not isinstance(text, str):
        return []

    if lower:
        text = text.lower()

    # Keep only letters, numbers and spaces
    if remove_punctuation:
        text = re.sub(r"[^a-z0-9\s]", " ", text)

    tokens = text.split()
    cleaned = []
    for tok in tokens:
        if len(tok) < min_token_len:
            continue
        if remove_stopwords and tok in _STOPWORDS:
            continue
        cleaned.append(tok)
    return cleaned


def preprocess_texts(
    texts: Dict[str, str],
    *,
    lower: bool = True,
    remove_punctuation: bool = True,
    remove_stopwords: bool = True,
) -> Dict[str, List[str]]:
    """
    Apply tokenize_and_clean to every value in a {id: raw_text} mapping.
    """
    result = {}
    for key, raw in texts.items():
        result[key] = tokenize_and_clean(
            raw,
            lower=lower,
            remove_punctuation=remove_punctuation,
            remove_stopwords=remove_stopwords,
        )
    non_empty = sum(1 for v in result.values() if v)
    logger.debug("Preprocessed %d texts (%d non-empty)", len(result), non_empty)
    return result


def tokens_to_string(tokens: List[str]) -> str:
    """Re-join tokens into a single string (useful for embedding models)."""
    return " ".join(tokens)