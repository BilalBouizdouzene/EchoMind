"""Small opt-in logging configuration for local runs and reproducible reports."""

from __future__ import annotations

import logging
import os


def configure_logging(level: str | None = None) -> None:
    """Configure one concise stderr handler without changing library defaults."""
    selected = (level or os.getenv("ECHOMIND_LOG_LEVEL", "INFO")).upper()
    numeric = getattr(logging, selected, logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
