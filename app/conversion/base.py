"""Conversion abstractions.

AbstractConverter   — structural Protocol all converters must implement.
ConversionResult    — typed output of any converter.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ConversionResult(BaseModel):
    """Output from a document converter."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    text_content: str
    markdown_content: str = ""
    page_count: int | None = None
    converter_used: str = ""
    warnings: list[str] = Field(default_factory=list)
    converted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class AbstractConverter(Protocol):
    """Structural protocol for document converters."""

    async def convert(self, file_path: str, document_id: UUID) -> ConversionResult:
        """Convert the file at *file_path* to text/markdown.

        Parameters
        ----------
        file_path:
            Absolute path to the source file.
        document_id:
            UUID of the already-ingested DocumentMetadata record.

        Returns
        -------
        ConversionResult
            Always populated. Failures go into ``warnings``; raise
            ``ConversionError`` only for irrecoverable errors.
        """
        ...
