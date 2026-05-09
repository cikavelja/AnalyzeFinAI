"""File type detector — determines MIME type and extension from a file path."""
from __future__ import annotations

import mimetypes
from pathlib import Path

import structlog

from app.exceptions import IngestionError

logger = structlog.get_logger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf", ".docx", ".xlsx", ".csv", ".pptx",
        ".txt", ".md", ".html", ".htm", ".json",
        ".xml", ".png", ".jpg", ".jpeg", ".zip",
    }
)


def detect_file_type(file_path: str) -> tuple[str, str]:
    """Return (extension, mime_type) for the file at *file_path*.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the file.

    Returns
    -------
    tuple[str, str]
        (extension_lower, mime_type) e.g. (".pdf", "application/pdf").

    Raises
    ------
    IngestionError
        If the file does not exist or has an unsupported extension.
    """
    path = Path(file_path)
    if not path.exists():
        raise IngestionError(f"File not found: {file_path}")
    if not path.is_file():
        raise IngestionError(f"Path is not a regular file: {file_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise IngestionError(
            f"Unsupported file extension '{ext}'. "
            f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "application/octet-stream"

    logger.debug("file_type_detected", file=file_path, ext=ext, mime=mime_type)
    return ext, mime_type
