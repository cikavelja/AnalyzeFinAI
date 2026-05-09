"""Document-level Pydantic models.

DocumentMetadata   — immutable metadata for an ingested file.
DocumentChunk      — a text slice of a converted document ready for analysis.
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Immutable metadata recorded at ingestion time."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    file_name: str
    file_size: int  # bytes
    extension: str  # e.g. ".pdf"
    mime_type: str | None = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_path: str | None = None


class DocumentChunk(BaseModel):
    """A contiguous slice of text extracted from a converted document."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    index: int  # zero-based position within document
    text: str
    page_number: int | None = None
    section_title: str | None = None
    word_count: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
