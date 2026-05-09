"""Text chunker — splits long document text into overlapping DocumentChunks.

Uses a simple character-based sliding window. Token-aware chunking
(via tiktoken) can be added in a later phase.
"""
from __future__ import annotations

from uuid import UUID

import structlog

from app.models.document import DocumentChunk

logger = structlog.get_logger(__name__)

DEFAULT_CHUNK_SIZE = 2000   # characters per chunk
DEFAULT_CHUNK_OVERLAP = 200  # characters of overlap between chunks


def chunk_text(
    text: str,
    document_id: UUID,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    """Split *text* into overlapping DocumentChunk records.

    Parameters
    ----------
    text:
        The full document text to split.
    document_id:
        UUID of the parent document (used to populate DocumentChunk.document_id).
    chunk_size:
        Maximum number of characters per chunk.
    overlap:
        Number of characters to repeat at the start of each subsequent chunk
        to preserve context across boundaries.

    Returns
    -------
    list[DocumentChunk]
        Ordered list of chunks. Returns a single empty chunk if *text* is blank.
    """
    if not text or not text.strip():
        logger.warning("chunker_empty_text", document_id=str(document_id))
        return [
            DocumentChunk(
                document_id=document_id,
                index=0,
                text="",
            )
        ]

    chunks: list[DocumentChunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text_slice = text[start:end]

        chunks.append(
            DocumentChunk(
                document_id=document_id,
                index=index,
                text=chunk_text_slice,
                token_count=len(chunk_text_slice.split()),  # rough word count
            )
        )

        if end >= len(text):
            break

        start = end - overlap
        index += 1

    logger.debug("chunker_done", document_id=str(document_id), chunks=len(chunks))
    return chunks
