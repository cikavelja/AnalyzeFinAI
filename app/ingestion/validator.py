"""Ingestion validator — checks file size and basic integrity before processing."""
from __future__ import annotations

from pathlib import Path

import structlog

from app.exceptions import IngestionError

logger = structlog.get_logger(__name__)

MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB


def validate_file(file_path: str, max_size: int = MAX_FILE_SIZE_BYTES) -> None:
    """Validate that *file_path* exists, is readable, and is within size limits.

    Parameters
    ----------
    file_path:
        Path to the file to validate.
    max_size:
        Maximum allowed file size in bytes (default 100 MB).

    Raises
    ------
    IngestionError
        If the file fails any validation check.
    """
    path = Path(file_path)

    if not path.exists():
        raise IngestionError(f"File does not exist: {file_path}")

    if not path.is_file():
        raise IngestionError(f"Not a regular file: {file_path}")

    size = path.stat().st_size
    if size == 0:
        raise IngestionError(f"File is empty (0 bytes): {file_path}")

    if size > max_size:
        raise IngestionError(
            f"File too large: {size:,} bytes (max {max_size:,} bytes): {file_path}"
        )

    logger.debug("file_validated", file=file_path, size=size)
