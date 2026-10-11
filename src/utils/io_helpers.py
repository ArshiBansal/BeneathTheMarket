"""
Small I/O utilities for JSON, joblib and directory management.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import joblib

logger = logging.getLogger(__name__)


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Create a directory (and parents) if it does not exist.
    Returns the Path object for convenience.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_json(
    obj: Any,
    path: Union[str, Path],
    *,
    indent: int = 2,
    default: Any = str,
) -> Path:
    """
    Write a JSON-serialisable object to disk.
    Non-serialisable values are converted with `default` (str by default).
    """
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=indent, default=default)
    logger.debug("Saved JSON → %s", path)
    return path


def load_json(path: Union[str, Path]) -> Any:
    """Load a JSON file and return the parsed object."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("Loaded JSON ← %s", path)
    return data


def save_joblib(
    obj: Any,
    path: Union[str, Path],
    *,
    compress: int = 3,
) -> Path:
    """
    Persist an arbitrary Python object with joblib.
    """
    path = Path(path)
    ensure_dir(path.parent)
    joblib.dump(obj, path, compress=compress)
    logger.debug("Saved joblib → %s", path)
    return path


def load_joblib(path: Union[str, Path]) -> Any:
    """Load a joblib-serialised object."""
    path = Path(path)
    obj = joblib.load(path)
    logger.debug("Loaded joblib ← %s", path)
    return obj


def safe_filename(name: str, max_len: int = 120) -> str:
    """
    Convert an arbitrary string into a filesystem-safe filename
    (keeps alphanumeric, dash, underscore and dot).
    """
    import re
    cleaned = re.sub(r"[^\w.\-]", "_", name)
    return cleaned[:max_len]