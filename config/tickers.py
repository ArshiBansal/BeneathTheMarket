"""
Initial candidate company universe (37 tickers across 6 categories).

This list is taken directly from the project proposal (Appendix A).
Tickers must be validated during the feasibility phase against
yfinance availability, listing status and history length.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# ----------------------------------------------------------------------
# Category → list of tickers
# ----------------------------------------------------------------------
CATEGORIES: Dict[str, List[str]] = {
    "Major technology platforms": [
        "AAPL",   # Apple
        "MSFT",   # Microsoft
        "AMZN",   # Amazon
        "GOOGL",  # Alphabet
        "META",   # Meta Platforms
        "NFLX",   # Netflix
    ],
    "Semiconductors and chip design": [
        "NVDA",   # NVIDIA
        "AMD",    # AMD
        "AVGO",   # Broadcom
        "QCOM",   # Qualcomm
        "INTC",   # Intel
        "MU",     # Micron
        "TXN",    # Texas Instruments
    ],
    "Cloud and enterprise infrastructure": [
        "ORCL",   # Oracle
        "IBM",    # IBM
        "CSCO",   # Cisco
        "ANET",   # Arista Networks
        "DELL",   # Dell Technologies
        "HPE",    # Hewlett Packard Enterprise
    ],
    "Enterprise software and developer platforms": [
        "TEAM",   # Atlassian
        "ADBE",   # Adobe
        "CRM",    # Salesforce
        "NOW",    # ServiceNow
        "SAP",    # SAP
        "ADSK",   # Autodesk
        "SNPS",   # Synopsys
        "CDNS",   # Cadence Design Systems
    ],
    "Fintech and digital financial infrastructure": [
        "PYPL",   # PayPal
        "XYZ",    # Block
        "FI",     # Fiserv
        "GPN",    # Global Payments
        "COIN",   # Coinbase
        "HOOD",   # Robinhood
    ],
    "Data, AI, and digital infrastructure software": [
        "PLTR",   # Palantir
        "SNOW",   # Snowflake
        "DDOG",   # Datadog
        "NET",    # Cloudflare
        "MDB",    # MongoDB
        "CRWD",   # CrowdStrike
    ],
}

# Flat list of all unique tickers (order preserved by category appearance)
TICKERS: List[str] = []
for _tickers in CATEGORIES.values():
    for t in _tickers:
        if t not in TICKERS:
            TICKERS.append(t)

# Reverse lookup: ticker → primary category
_TICKER_TO_CATEGORY: Dict[str, str] = {
    ticker: category
    for category, tickers in CATEGORIES.items()
    for ticker in tickers
}


def get_tickers_by_category(category: str) -> List[str]:
    """Return the list of tickers that belong to the given category."""
    return CATEGORIES.get(category, []).copy()


def get_primary_category(ticker: str) -> Optional[str]:
    """Return the primary category assigned to a ticker, or None if unknown."""
    return _TICKER_TO_CATEGORY.get(ticker.upper())


def get_all_categories() -> List[str]:
    """Return the ordered list of category names."""
    return list(CATEGORIES.keys())


def is_valid_ticker(ticker: str) -> bool:
    """Check whether a ticker belongs to the candidate universe."""
    return ticker.upper() in _TICKER_TO_CATEGORY