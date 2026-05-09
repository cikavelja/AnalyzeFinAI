"""AuditEvent model — every pipeline step emits one at start and one at end."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AuditEvent(BaseModel):
    """Immutable record of a single pipeline action for the audit log."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    event_type: str  # e.g. "ingestion", "conversion", "analysis", "routing"
    request_id: UUID | None = None
    status: str  # "started" | "completed" | "failed"
    detail: str = ""
    model_used: str | None = None
    duration_ms: float | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    extra: dict[str, str] = Field(default_factory=dict)
