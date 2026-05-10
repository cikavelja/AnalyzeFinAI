"""MCPConverter — delegates document conversion to a MarkItDown MCP server.

Used when CONVERSION_MODE=mcp. Falls back gracefully with a ConversionError
if the MCP server is unreachable.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

import httpx
import structlog

from app.audit.logger import audit_logger
from app.config import settings
from app.conversion.base import ConversionResult
from app.exceptions import ConversionError
from app.models.audit import AuditEvent

logger = structlog.get_logger(__name__)


class MCPConverter:
    """Converts documents via the MarkItDown MCP server."""

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or settings.mcp_endpoint

    async def convert(self, file_path: str, document_id: UUID) -> ConversionResult:
        """Send *file_path* to the MCP server and return the markdown result.

        Raises:
            ConversionError: if local_only_mode is set, the server is unreachable,
                             or the server returns an error.
        """
        if settings.local_only_mode:
            raise ConversionError(
                "LOCAL_ONLY_MODE is enabled — MCP conversion is blocked."
            )

        await audit_logger.emit(AuditEvent(
            event_type="conversion",
            status="started",
            detail=f"MCPConverter started: {file_path}",
        ))

        try:
            file_bytes = await asyncio.to_thread(Path(file_path).read_bytes)
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self._endpoint,
                    files={"file": (file_path, file_bytes)},
                )
                resp.raise_for_status()
                data = resp.json()

        except httpx.ConnectError as exc:
            raise ConversionError(
                f"MCP server not reachable at {self._endpoint}: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ConversionError(f"MCP server HTTP error: {exc}") from exc
        except OSError as exc:
            raise ConversionError(f"Cannot open file '{file_path}': {exc}") from exc

        markdown = data.get("markdown", "")
        text = data.get("text", markdown)

        logger.info("mcp_converter_success", file=file_path, chars=len(markdown))

        await audit_logger.emit(AuditEvent(
            event_type="conversion",
            status="completed",
            detail=f"MCPConverter completed: {file_path} ({len(markdown)} chars)",
        ))

        return ConversionResult(
            document_id=document_id,
            text_content=text,
            markdown_content=markdown,
            page_count=data.get("page_count"),
            converter_used="MCPConverter",
        )
