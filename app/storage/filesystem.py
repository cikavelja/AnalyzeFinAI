"""FilesystemStorage — persists converted document content to local disk."""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

import structlog

from app.exceptions import IngestionError

logger = structlog.get_logger(__name__)

_DEFAULT_BASE_DIR = "data/converted"


class FilesystemStorage:
    """Stores and retrieves document text on the local filesystem."""

    def __init__(self, base_dir: str = _DEFAULT_BASE_DIR) -> None:
        self._base = Path(base_dir)

    async def save(self, document_id: UUID, content: str, suffix: str = ".md") -> str:
        """Write *content* to disk and return the relative storage key."""
        self._base.mkdir(parents=True, exist_ok=True)
        key = f"{document_id}{suffix}"
        path = self._base / key
        path.write_text(content, encoding="utf-8")
        logger.debug("storage_saved", key=key, size=len(content))
        return str(path)

    def key_for(self, document_id: UUID, suffix: str = ".md") -> str:
        """Return the absolute storage key for *document_id* without touching the filesystem."""
        return str(self._base / f"{document_id}{suffix}")

    async def load(self, storage_key: str) -> str:
        """Read and return the content at *storage_key*."""
        path = Path(storage_key)
        if not path.exists():
            raise IngestionError(f"Storage key not found: {storage_key}")
        return path.read_text(encoding="utf-8")

    async def exists(self, storage_key: str) -> bool:
        """Return True if the storage key exists on disk."""
        return Path(storage_key).exists()
