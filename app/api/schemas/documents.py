"""API schemas for document upload endpoints."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Returned by POST /api/v1/documents/upload."""

    document_id: UUID
    file_name: str
    file_size: int
