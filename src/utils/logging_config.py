"""
Centralised logging configuration.

Call `setup_logging()` once at the start of a notebook, script or
Streamlit session.  Subsequent calls are safe (idempotent).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from config import settings


_CONFIGURED = False


def setup_logging(
    level: Optional[str] = None,
    *,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None,
) -> None:
    """
    Configure the root logger.

    Parameters
    ----------
    level : str, optional
        Logging level (DEBUG, INFO, WARNING, ERROR).  Defaults to
        the value in settings.LOG_LEVEL.
    log_to_file : bool
        If True, also write logs to a rotating file under logs/.
    log_dir : Path, optional
        Override the default logs directory.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = (level or settings.LOG_LEVEL).upper()
    numeric_level = getattr(logging, level, logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Clear any existing handlers to avoid duplicate output
    for h in root.handlers[:]:
        root.removeHandler(h)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(numeric_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # Optional file handler
    if log_to_file:
        log_dir = log_dir or settings.LOGS_DIR
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / "app.log",
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

    _CONFIGURED = True
    logging.getLogger(__name__).debug(
        "Logging configured (level=%s, file=%s)", level, log_to_file
    )


def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper that ensures logging is configured
    before returning a named logger.
    """
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)