"""LocalConverter — reads a file as plain text without any external service.

This is the default converter used when CONVERSION_MODE=local.
Supported file types: .txt, .md, .csv, .json, .xml, .html (raw text pass-through).
For other types, the raw bytes are decoded with errors='replace'.
ZIP files are explicitly rejected — use CONVERSION_MODE=markitdown for ZIP support.
"""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

import structlog

from app.audit.logger import audit_logger
from app.conversion.base import ConversionResult
from app.exceptions import ConversionError
from app.models.audit import AuditEvent

logger = structlog.get_logger(__name__)

# Extensions treated as plain-text
_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"}


class LocalConverter:
    """Reads a file and returns its text content without an external service."""

    async def convert(self, file_path: str, document_id: UUID) -> ConversionResult:
        """Convert the file at *file_path* to a ConversionResult.

        Raises:
            ConversionError: if the file does not exist, cannot be read, or is a ZIP.
        """
        await audit_logger.emit(AuditEvent(
            event_type="conversion",
            status="started",
            detail=f"LocalConverter started: {file_path}",
        ))

        path = Path(file_path)
        if not path.exists():
            raise ConversionError(f"File not found: {file_path}")
        if not path.is_file():
            raise ConversionError(f"Path is not a file: {file_path}")

        warnings: list[str] = []
        ext = path.suffix.lower()

        if ext == ".zip":
            raise ConversionError(
                "ZIP files are not supported in local conversion mode. "
                "Set CONVERSION_MODE=markitdown to enable ZIP support."
            )

        try:
            if ext in _TEXT_EXTENSIONS:
                text = path.read_text(encoding="utf-8", errors="replace")
            else:
                # Best-effort: decode bytes as UTF-8
                raw = path.read_bytes()
                text = raw.decode("utf-8", errors="replace")
                warnings.append(
                    f"Extension '{ext}' is not natively supported by LocalConverter. "
                    "Content decoded as UTF-8 with replacement characters for invalid bytes."
                )
        except OSError as exc:
            raise ConversionError(f"Cannot read file '{file_path}': {exc}") from exc

        logger.info("local_converter_success", file=file_path, chars=len(text))

        await audit_logger.emit(AuditEvent(
            event_type="conversion",
            status="completed",
            detail=f"LocalConverter completed: {file_path} ({len(text)} chars)",
        ))

        return ConversionResult(
            document_id=document_id,
            text_content=text,
            markdown_content=text,  # no markdown conversion in local mode
            converter_used="LocalConverter",
            warnings=warnings,
        )
