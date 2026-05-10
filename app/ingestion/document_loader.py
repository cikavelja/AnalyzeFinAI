"""Shared document loading helper used by the API route, CLI, and agent tools.

Provides:
    load_chunks(document_ids, upload_dir)  — convert + chunk multiple docs by UUID
    load_chunks_from_path(file_path)       — convert + chunk a single file by path
"""
from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import structlog

from app.conversion import get_converter
from app.models.document import DocumentChunk
from app.storage.base import AbstractStorage
from app.storage.filesystem import FilesystemStorage

logger = structlog.get_logger(__name__)

_DEFAULT_UPLOAD_DIR = Path("data/uploads")
_storage: AbstractStorage = FilesystemStorage()

# In-process chunk cache keyed by document_id string (cleared on process restart)
_chunk_cache: dict[str, list[DocumentChunk]] = {}


async def load_chunks(
    document_ids: list[UUID],
    upload_dir: Path = _DEFAULT_UPLOAD_DIR,
) -> list[DocumentChunk]:
    """Convert and chunk uploaded documents by their UUID.

    Files must have been saved as ``<document_id>.<ext>`` in *upload_dir*
    (which is guaranteed by the upload route).  Unknown or unconvertible
    documents are skipped with a warning.

    Converted markdown is cached in ``data/converted/`` so subsequent calls
    for the same document do not re-convert the source file.

    Returns
    -------
    list[DocumentChunk]
        All chunks from all matched documents, in document order.
    """
    if not document_ids:
        return []

    from app.chunking.chunker import chunk_text  # noqa: PLC0415

    converter = get_converter()
    chunks: list[DocumentChunk] = []

    for doc_id in document_ids:
        cache_key = str(doc_id)

        # In-process cache hit
        if cache_key in _chunk_cache:
            logger.debug("loader_chunk_cache_hit", document_id=cache_key)
            chunks.extend(_chunk_cache[cache_key])
            continue

        # Filesystem cache hit: load pre-converted markdown
        storage_key = _storage.key_for(doc_id)
        if await _storage.exists(storage_key):
            try:
                text = await _storage.load(storage_key)
                doc_chunks = chunk_text(text, doc_id)
                _chunk_cache[cache_key] = doc_chunks
                chunks.extend(doc_chunks)
                logger.debug("loader_storage_cache_hit", document_id=cache_key)
                continue
            except Exception as exc:
                logger.warning("loader_storage_cache_load_failed", document_id=cache_key, error=str(exc))

        matches = list(upload_dir.glob(f"{doc_id}.*"))
        if not matches:
            logger.warning("loader_document_not_found", document_id=cache_key)
            continue
        try:
            result = await converter.convert(str(matches[0]), doc_id)
            # Persist converted markdown for future cache hits
            try:
                await _storage.save(doc_id, result.text_content)
            except Exception as exc:
                logger.warning("loader_storage_save_failed", document_id=cache_key, error=str(exc))
            doc_chunks = chunk_text(result.text_content, doc_id)
            _chunk_cache[cache_key] = doc_chunks
            chunks.extend(doc_chunks)
        except Exception as exc:
            logger.error("loader_conversion_failed", document_id=cache_key, error=str(exc))

    return chunks


async def load_chunks_from_path(file_path: str) -> list[DocumentChunk]:
    """Convert and chunk a single file by its filesystem path.

    Used by the CLI ``analyze --file`` command where no document_id exists yet.
    A temporary UUID is generated for the chunk document_id field.

    Returns
    -------
    list[DocumentChunk]
        Ordered chunks of the converted document.  Empty on conversion failure.
    """
    from app.chunking.chunker import chunk_text  # noqa: PLC0415

    converter = get_converter()
    doc_id = uuid4()
    try:
        result = await converter.convert(file_path, doc_id)
        return chunk_text(result.text_content, doc_id)
    except Exception as exc:
        logger.error("loader_path_conversion_failed", file=file_path, error=str(exc))
        return []
