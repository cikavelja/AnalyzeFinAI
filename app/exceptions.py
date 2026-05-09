"""Typed exceptions for AnalizerAI.

All application exceptions live here. Never raise a bare ``Exception("message")``.
"""
from __future__ import annotations


class AnalizerAIError(Exception):
    """Base class for all AnalizerAI errors."""


class CalculationError(AnalizerAIError):
    """Raised when the financial calculation engine encounters an unrecoverable error.

    Examples:
    - Required column missing from the input DataFrame.
    - Unexpected data type that prevents numpy/pandas operations.
    """


class ConversionError(AnalizerAIError):
    """Raised when document conversion fails.

    Examples:
    - Unsupported file format.
    - External MCP server unavailable.
    - Corrupted file content.
    """


class AnalysisError(AnalizerAIError):
    """Raised when an analyzer encounters an unrecoverable error.

    Examples:
    - LLM response unparseable.
    - Required pre-processing step not completed.
    """


class IngestionError(AnalizerAIError):
    """Raised when document ingestion fails.

    Examples:
    - File not found.
    - File too large.
    - Unsupported MIME type.
    """


class ValidationError(AnalizerAIError):
    """Raised when input validation fails."""


class RoutingError(AnalizerAIError):
    """Raised when the router cannot determine an analysis type."""
