"""MCPConverter — delegates document conversion to a MarkItDown MCP server.

Used when CONVERSION_MODE=mcp. Falls back gracefully with a ConversionError
if the MCP server is unreachable.
"""
from __future__ import annotations

from uuid import UUID

import httpx
import structlog

from app.config import settings
from app.conversion.base import ConversionResult
from app.exceptions import ConversionError

logger = structlog.get_logger(__name__)

_MCP_ENDPOINT = "http://localhost:3001/convert"  # Override via env if needed


class MCPConverter:
    """Converts documents via the MarkItDown MCP server."""

    def __init__(self, endpoint: str = _MCP_ENDPOINT) -> None:
        self._endpoint = endpoint

    async def convert(self, file_path: str, document_id: UUID) -> ConversionResult:
        """Send *file_path* to the MCP server and return the markdown result.

        Raises:
            ConversionError: if the server is unreachable or returns an error.
        """
        if settings.local_only_mode:
            raise ConversionError(
                "LOCAL_ONLY_MODE is enabled — MCP conversion is blocked."
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                with open(file_path, "rb") as fh:
                    resp = await client.post(
                        self._endpoint,
                        files={"file": (file_path, fh)},
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

        return ConversionResult(
            document_id=document_id,
            text_content=text,
            markdown_content=markdown,
            page_count=data.get("page_count"),
            converter_used="MCPConverter",
        )
