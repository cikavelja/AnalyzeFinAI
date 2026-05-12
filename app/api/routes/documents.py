"""Documents route — POST /api/v1/documents/upload, DELETE /api/v1/documents/{document_id}.

Accepts a file upload, validates it via the ingestion pipeline, and returns
a document_id that can be passed to POST /api/v1/analyze.
"""
from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas.documents import UploadResponse
from app.exceptions import IngestionError
from app.ingestion.document_loader import evict_chunk_cache
from app.ingestion.loader import load_document

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["documents"])

_UPLOAD_DIR = Path("data/uploads")

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """Save an uploaded file to disk and return its document_id."""
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    original_name = file.filename or "upload"
    suffix = Path(original_name).suffix.lower()
    tmp_path = _UPLOAD_DIR / f"{uuid4()}{suffix}"

    # CRIT-2: Check Content-Length / file.size BEFORE reading into memory
    if file.size is not None and file.size > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file.size} bytes). Maximum allowed: {_MAX_UPLOAD_BYTES} bytes.",
        )

    try:
        # Read in chunks to avoid OOM on files without a Content-Length header
        chunks: list[bytes] = []
        total_read = 0
        while True:
            chunk = await file.read(65536)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > _MAX_UPLOAD_BYTES:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size of {_MAX_UPLOAD_BYTES} bytes.",
                )
            chunks.append(chunk)
        content = b"".join(chunks)
        tmp_path.write_bytes(content)

        metadata = await load_document(str(tmp_path))

        # Rename to document_id so the analyze route can look it up later
        final_path = _UPLOAD_DIR / f"{metadata.id}{suffix}"
        tmp_path.rename(final_path)

        try:
            logger.info(
                "api_upload_ok",
                document_id=str(metadata.id),
                file=original_name,
                size=metadata.file_size,
            )

            return UploadResponse(
                document_id=metadata.id,
                file_name=original_name,
                file_size=metadata.file_size,
            )
        except Exception:
            final_path.unlink(missing_ok=True)
            raise

    except HTTPException:
        raise
    except IngestionError as exc:
        tmp_path.unlink(missing_ok=True)
        logger.warning("api_upload_validation_error", error=str(exc), file=original_name)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        logger.error("api_upload_error", error=str(exc), file=original_name)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: UUID) -> None:
    """Delete an uploaded document and its converted artefacts."""
    upload_dir = Path("data/uploads")
    converted_dir = Path("data/converted")

    deleted_any = False
    for path in list(upload_dir.glob(f"{document_id}.*")) + list(converted_dir.glob(f"{document_id}.*")):
        path.unlink(missing_ok=True)
        deleted_any = True
        logger.info("api_document_deleted", path=str(path))

    if not deleted_any:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    evict_chunk_cache(str(document_id))
