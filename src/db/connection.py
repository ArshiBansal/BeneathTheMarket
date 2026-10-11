"""
MongoDB connection helpers – LOCALHOST ONLY.

"""

from __future__ import annotations

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """
    Return a singleton MongoClient connected to the local MongoDB instance.

    Raises
    ------
    ConnectionFailure
        If the local server is unreachable.
    """
    global _client
    if _client is None:
        try:
            _client = MongoClient(**settings.mongo_connection_kwargs)
            # Force a server selection to fail fast if MongoDB is down
            _client.admin.command("ping")
            logger.info(
                "Connected to local MongoDB at %s (db=%s)",
                settings.MONGODB_URI,
                settings.MONGODB_DB_NAME,
            )
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            logger.error("Cannot connect to local MongoDB: %s", exc)
            raise ConnectionFailure(
                f"Local MongoDB is not reachable at {settings.MONGODB_URI}. "
                "Make sure mongod is running on localhost."
            ) from exc
    return _client


def get_db() -> Database:
    """Return the project database handle."""
    client = get_client()
    return client[settings.MONGODB_DB_NAME]


def close_client() -> None:
    """Close the global client (useful in scripts / tests)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed.")