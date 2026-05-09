"""Storage abstractions — AbstractStorage protocol and filesystem implementation."""
from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class AbstractStorage(Protocol):
    """Structural protocol for document storage backends."""

    async def save(self, document_id: UUID, content: str, suffix: str = ".md") -> str:
        """Persist *content* and return the storage key / path."""
        ...

    async def load(self, storage_key: str) -> str:
        """Load and return content identified by *storage_key*."""
        ...

    async def exists(self, storage_key: str) -> bool:
        """Return True if the storage key exists."""
        ...
