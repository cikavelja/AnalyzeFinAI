"""Audit logger — append-only JSONL writer for AuditEvent records.

Every pipeline step must emit two events: one at the start and one at the end.

Usage::

    from app.audit.logger import audit_logger
    from app.models import AuditEvent

    await audit_logger.emit(AuditEvent(
        event_type="analysis",
        request_id=request.id,
        status="started",
        detail="SummaryAnalyzer started",
    ))
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import structlog

from app.config import settings
from app.models.audit import AuditEvent

logger = structlog.get_logger(__name__)


class AuditLogger:
    """Thread-safe, async-compatible append-only JSONL audit logger."""

    def __init__(self, log_path: str | None = None) -> None:
        self._path = Path(log_path or settings.audit_log_path)
        self._lock = asyncio.Lock()

    async def emit(self, event: AuditEvent) -> None:
        """Append *event* as a single JSON line to the audit log file.

        Creates parent directories on first write. Never raises — errors are
        logged via structlog but do not interrupt the calling pipeline.
        """
        try:
            async with self._lock:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                line = event.model_dump_json() + "\n"
                await asyncio.get_running_loop().run_in_executor(
                    None, self._append_sync, line
                )
            logger.debug(
                "audit_event_emitted",
                event_type=event.event_type,
                status=event.status,
                request_id=str(event.request_id) if event.request_id else None,
            )
        except Exception as exc:  # pragma: no cover
            logger.error("audit_emit_failed", error=str(exc))

    def _append_sync(self, line: str) -> None:
        """Synchronous file append — called from executor."""
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line)


# Module-level singleton
audit_logger = AuditLogger()
