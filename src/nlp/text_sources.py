"""
Non-news textual sources for the NLP component.

Primary source strategy
-----------------------
1. Prefer short business descriptions already stored in company_metadata
   (populated from yfinance .info during ingestion).
2. Fall back to a small, static, hand-curated dictionary of sector /
   category descriptions that ship with the project (no external API,
   no news).
3. If neither is available the function returns an empty string and the
   caller is expected to document the limitation.

Never fetches news articles or social-media content.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from config.tickers import CATEGORIES, TICKERS, get_primary_category
from src.db.company_metadata import get_company_metadata, get_all_company_metadata

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Static, non-news category descriptions (project-owned text)
# ------------------------------------------------------------------
CATEGORY_DESCRIPTIONS: Dict[str, str] = {
    "Major technology platforms": (
        "Large diversified technology platforms that operate consumer and "
        "enterprise digital ecosystems, including operating systems, cloud "
        "services, digital advertising, e-commerce and content distribution."
    ),
    "Semiconductors and chip design": (
        "Companies that design, manufacture or supply semiconductors, "
        "graphics processors, chipsets and related intellectual property "
        "used in computing, mobile, automotive and data-centre applications."
    ),
    "Cloud and enterprise infrastructure": (
        "Providers of enterprise hardware, networking, storage, systems "
        "software and hybrid-cloud infrastructure that underpin corporate "
        "IT environments and large-scale data centres."
    ),
    "Enterprise software and developer platforms": (
        "Vendors of business application software, design tools, developer "
        "platforms, collaboration suites and electronic-design automation "
        "software used by enterprises and engineering teams."
    ),
    "Fintech and digital financial infrastructure": (
        "Companies that deliver digital payments, online brokerage, "
        "banking infrastructure, cryptocurrency exchange services and "
        "related financial technology platforms."
    ),
    "Data, AI, and digital infrastructure software": (
        "Software firms focused on data platforms, analytics, artificial "
        "intelligence infrastructure, observability, cybersecurity and "
        "edge or content-delivery networking."
    ),
}


def get_text_for_ticker(ticker: str) -> str:
    """
    Return the best available non-news description for a single ticker.

    Priority
    --------
    1. long_name + sector + industry from company_metadata
    2. static category description
    3. empty string
    """
    ticker = ticker.upper()
    meta = get_company_metadata(ticker) or {}

    parts: List[str] = []
    if meta.get("long_name"):
        parts.append(str(meta["long_name"]))
    if meta.get("short_name") and meta.get("short_name") != meta.get("long_name"):
        parts.append(str(meta["short_name"]))
    if meta.get("sector"):
        parts.append(f"Sector: {meta['sector']}")
    if meta.get("industry"):
        parts.append(f"Industry: {meta['industry']}")

    if parts:
        return ". ".join(parts) + "."

    # Fallback to category description
    category = get_primary_category(ticker)
    if category and category in CATEGORY_DESCRIPTIONS:
        return CATEGORY_DESCRIPTIONS[category]

    logger.debug("No text source found for %s", ticker)
    return ""


def load_company_texts(
    tickers: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Build a dictionary {ticker: description} for the requested universe.

    Missing descriptions are stored as empty strings so that downstream
    code can detect and report coverage gaps.
    """
    tickers = tickers or TICKERS
    texts: Dict[str, str] = {}
    for t in tickers:
        texts[t.upper()] = get_text_for_ticker(t)
    coverage = sum(1 for v in texts.values() if v.strip())
    logger.info(
        "Loaded non-news text for %d/%d tickers",
        coverage,
        len(texts),
    )
    return texts


def load_category_texts() -> Dict[str, str]:
    """Return the static category description dictionary."""
    return CATEGORY_DESCRIPTIONS.copy()