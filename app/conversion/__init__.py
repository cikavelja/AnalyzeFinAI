# app/conversion/__init__.py
"""Converter factory — single source of truth for converter selection."""
from __future__ import annotations

from app.config import settings
from app.conversion.base import ConversionResult  # re-export for convenience


def get_converter():
    """Return the configured converter instance based on ``CONVERSION_MODE``."""
    if settings.conversion_mode == "mcp":
        from app.conversion.mcp_converter import MCPConverter  # noqa: PLC0415
        return MCPConverter()
    if settings.conversion_mode == "markitdown":
        from app.conversion.markitdown_converter import MarkitdownConverter  # noqa: PLC0415
        return MarkitdownConverter()
    from app.conversion.local_converter import LocalConverter  # noqa: PLC0415
    return LocalConverter()


__all__ = ["get_converter", "ConversionResult"]
