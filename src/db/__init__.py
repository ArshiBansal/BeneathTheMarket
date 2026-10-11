"""
Local MongoDB data-access layer (PyMongo).

All modules connect exclusively to a locally running MongoDB Community
Server.

Public API
----------
from src.db import get_client, get_db, COLLECTIONS
from src.db.market_data import upsert_market_data, get_market_data
...
"""

from .connection import get_client, get_db, close_client
from .collections import COLLECTIONS, ensure_indexes

__all__ = [
    "get_client",
    "get_db",
    "close_client",
    "COLLECTIONS",
    "ensure_indexes",
]