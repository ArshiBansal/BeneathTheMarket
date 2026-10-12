"""
Non-news NLP helpers for the Streamlit app.

All text comes from company/category descriptions already stored
or shipped with the project – never from news feeds.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import TICKERS
from config.tickers import get_primary_category
from src.nlp.text_sources import (
    load_company_texts,
    load_category_texts,
    get_text_for_ticker,
)
from src.nlp.preprocessing import preprocess_texts, tokenize_and_clean
from src.nlp.embeddings import embed_texts
from src.nlp.similarity import (
    compute_similarity_matrix,
    most_similar_companies,
    keyword_overlap_score,
)

logger = logging.getLogger(__name__)


class NLPService:
    """Lightweight NLP operations exposed to Streamlit pages."""

    def __init__(self) -> None:
        self._texts: Dict[str, str] = {}
        self._sim_matrix: Optional[pd.DataFrame] = None
        self._ids: List[str] = []
        self._embeddings: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Text access
    # ------------------------------------------------------------------
    def get_description(self, ticker: str) -> str:
        return get_text_for_ticker(ticker)

    def get_category_descriptions(self) -> Dict[str, str]:
        return load_category_texts()

    def load_texts(self, tickers: Optional[List[str]] = None) -> Dict[str, str]:
        tickers = tickers or list(TICKERS)
        self._texts = load_company_texts(tickers=tickers)
        return self._texts

    def coverage(self, tickers: Optional[List[str]] = None) -> pd.DataFrame:
        texts = self.load_texts(tickers)
        rows = []
        for t, txt in texts.items():
            rows.append({
                "ticker": t,
                "category": get_primary_category(t),
                "has_text": bool(txt and txt.strip()),
                "length": len(txt) if txt else 0,
                "preview": (txt[:80] + "…") if txt and len(txt) > 80 else txt,
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Similarity
    # ------------------------------------------------------------------
    def build_similarity(
        self,
        tickers: Optional[List[str]] = None,
        prefer_sentence_transformers: bool = True,
    ) -> pd.DataFrame:
        texts = self.load_texts(tickers)
        nonempty = {t: v for t, v in texts.items() if v and v.strip()}
        if len(nonempty) < 2:
            logger.warning("Not enough texts to build similarity matrix")
            self._sim_matrix = pd.DataFrame()
            return self._sim_matrix

        ids, emb = embed_texts(
            nonempty,
            prefer_sentence_transformers=prefer_sentence_transformers,
        )
        self._ids = ids
        self._embeddings = emb
        self._sim_matrix = compute_similarity_matrix(ids, emb)
        return self._sim_matrix

    def most_similar(
        self,
        ticker: str,
        top_n: int = 5,
    ) -> List[Tuple[str, float]]:
        if self._sim_matrix is None or self._sim_matrix.empty:
            self.build_similarity()
        if self._sim_matrix is None or self._sim_matrix.empty:
            return []
        return most_similar_companies(self._sim_matrix, ticker, top_n=top_n)

    def similarity_matrix(self) -> pd.DataFrame:
        if self._sim_matrix is None:
            self.build_similarity()
        return self._sim_matrix if self._sim_matrix is not None else pd.DataFrame()

    # ------------------------------------------------------------------
    # Keyword overlap (transparent baseline)
    # ------------------------------------------------------------------
    def keyword_overlap(self, ticker_a: str, ticker_b: str) -> float:
        texts = self._texts or self.load_texts([ticker_a, ticker_b])
        tok_a = tokenize_and_clean(texts.get(ticker_a, ""))
        tok_b = tokenize_and_clean(texts.get(ticker_b, ""))
        return keyword_overlap_score(tok_a, tok_b)

    # ------------------------------------------------------------------
    # Summary for UI cards
    # ------------------------------------------------------------------
    def summary(self, tickers: Optional[List[str]] = None) -> Dict[str, Any]:
        cov = self.coverage(tickers)
        n_with = int(cov["has_text"].sum()) if not cov.empty else 0
        return {
            "n_tickers": len(cov),
            "n_with_text": n_with,
            "coverage_pct": round(100 * n_with / max(len(cov), 1), 1),
            "source": "yfinance company metadata + static category descriptions",
            "exclusions": "No news, no social media, no sentiment pipeline",
        }