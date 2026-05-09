"""Ingestion loader — creates DocumentMetadata records from validated files."""
from __future__ import annotations

from pathlib import Path

import structlog

from app.audit.logger import audit_logger
from app.ingestion.detector import detect_file_type
from app.ingestion.validator import validate_file
from app.models.audit import AuditEvent
from app.models.document import DocumentMetadata

logger = structlog.get_logger(__name__)


async def load_document(file_path: str) -> DocumentMetadata:
    """Validate, detect type, and create a DocumentMetadata record.

    Parameters
    ----------
    file_path:
        Absolute path to the file to ingest.

    Returns
    -------
    DocumentMetadata
        Immutable metadata record for the ingested file.

    Raises
    ------
    IngestionError
        If validation or type detection fails.
    """
    await audit_logger.emit(
        AuditEvent(
            event_type="ingestion",
            status="started",
            detail=f"Loading file: {file_path}",
        )
    )

    validate_file(file_path)
    ext, mime_type = detect_file_type(file_path)

    path = Path(file_path)
    metadata = DocumentMetadata(
        file_name=path.name,
        file_size=path.stat().st_size,
        extension=ext,
        mime_type=mime_type,
        source_path=str(path.resolve()),
    )

    await audit_logger.emit(
        AuditEvent(
            event_type="ingestion",
            status="completed",
            detail=f"Ingested '{path.name}' ({path.stat().st_size:,} bytes)",
        )
    )

    logger.info("document_loaded", document_id=str(metadata.id), file=file_path)
    return metadata
