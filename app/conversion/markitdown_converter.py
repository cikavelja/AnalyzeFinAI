"""MarkitdownConverter — converts documents to markdown using the markitdown library.

Used when CONVERSION_MODE=markitdown. Supports PDF, DOCX, XLSX, PPTX, images,
HTML, and more via the MarkItDown library (https://github.com/microsoft/markitdown).

The underlying library is synchronous; conversion runs in a thread pool to avoid
blocking the async event loop.
"""
from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path
from uuid import UUID

import structlog
from markitdown import MarkItDown

from app.audit.logger import audit_logger
from app.conversion.base import ConversionResult
from app.exceptions import ConversionError
from app.models.audit import AuditEvent

logger = structlog.get_logger(__name__)

_MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 500 MB zip-bomb limit


class MarkitdownConverter:
    """Converts documents to markdown using the MarkItDown library."""

    def __init__(self) -> None:
        self._md = MarkItDown()

    async def convert(self, file_path: str, document_id: UUID) -> ConversionResult:
        """Convert the file at *file_path* to markdown via MarkItDown.

        Raises:
            ConversionError: if the file does not exist, is a zip bomb, or MarkItDown fails.
        """
        await audit_logger.emit(AuditEvent(
            event_type="conversion",
            status="started",
            detail=f"MarkitdownConverter started: {file_path}",
        ))

        path = Path(file_path)
        if not path.exists():
            raise ConversionError(f"File not found: {file_path}")
        if not path.is_file():
            raise ConversionError(f"Path is not a file: {file_path}")

        # Zip-bomb pre-flight check + path traversal guard
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as zf:
                total_uncompressed = sum(e.file_size for e in zf.infolist())
                if total_uncompressed > _MAX_UNCOMPRESSED_BYTES:
                    raise ConversionError(
                        f"ZIP uncompressed size {total_uncompressed:,} bytes exceeds "
                        f"the {_MAX_UNCOMPRESSED_BYTES // (1024 * 1024)} MB limit."
                    )
                for entry in zf.infolist():
                    entry_path = Path(entry.filename)
                    if entry_path.is_absolute() or ".." in entry_path.parts:
                        raise ConversionError(
                            f"ZIP entry with dangerous path rejected: {entry.filename!r}"
                        )

        try:
            result = await asyncio.to_thread(self._md.convert, str(path))
        except Exception as exc:
            raise ConversionError(
                f"MarkItDown failed to convert '{file_path}': {exc}"
            ) from exc

        markdown = result.text_content or ""

        logger.info(
            "markitdown_converter_success",
            file=file_path,
            chars=len(markdown),
        )

        await audit_logger.emit(AuditEvent(
            event_type="conversion",
            status="completed",
            detail=f"MarkitdownConverter completed: {file_path} ({len(markdown)} chars)",
        ))

        return ConversionResult(
            document_id=document_id,
            text_content=markdown,
            markdown_content=markdown,
            converter_used="MarkitdownConverter",
        )
