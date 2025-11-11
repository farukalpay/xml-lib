"""Structured logging utilities for xml-lib."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def structured_log(
    logger: logging.Logger,
    level: str,
    message: str,
    phase: str | None = None,
    doc_id: str | None = None,
    **kwargs: Any,
) -> None:
    """Log a structured message with ISO timestamps and metadata.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        phase: Optional phase identifier
        doc_id: Optional document ID
        **kwargs: Additional metadata
    """
    log_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "message": message,
    }

    if phase:
        log_data["phase"] = phase
    if doc_id:
        log_data["doc_id"] = doc_id

    log_data.update(kwargs)

    log_func = getattr(logger, level.lower())
    log_func(json.dumps(log_data))


def setup_file_logger(log_file: Path, name: str = "xml-lib") -> logging.Logger:
    """Set up a file logger with JSON output.

    Args:
        log_file: Path to log file
        name: Logger name

    Returns:
        Configured logger
    """
    logger = get_logger(name)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(log_file)
    handler.setFormatter(
        logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": %(message)s}',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    logger.addHandler(handler)

    return logger
