"""
Non-news NLP component.

Scope (project proposal)
------------------------
- Uses only licensed / publicly available company or sector descriptions
- Never builds a news or news-sentiment pipeline
- Output is contextual analysis (keywords, topics, similarity to behaviour clusters)
  – not a causal explanation of price moves

Public API
----------
from src.nlp import (
    load_company_texts,
    preprocess_texts,
    embed_texts,
    compute_similarity_matrix,
    match_text_to_regimes,
)
"""

from .text_sources import load_company_texts, get_text_for_ticker
from .preprocessing import preprocess_texts, tokenize_and_clean
from .embeddings import embed_texts, get_embedding_model
from .similarity import (
    compute_similarity_matrix,
    most_similar_companies,
    match_text_to_regimes,
)

__all__ = [
    "load_company_texts",
    "get_text_for_ticker",
    "preprocess_texts",
    "tokenize_and_clean",
    "embed_texts",
    "get_embedding_model",
    "compute_similarity_matrix",
    "most_similar_companies",
    "match_text_to_regimes",
]