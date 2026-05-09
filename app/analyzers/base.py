"""AbstractAnalyzer — structural Protocol that all analyzer implementations must satisfy.

Usage::

    class MyAnalyzer:
        async def analyze(
            self,
            request: AnalysisRequest,
            chunks: list[DocumentChunk],
            metrics: FinancialMetrics | None = None,
        ) -> AnalysisResult:
            ...
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.analysis import AnalysisRequest, AnalysisResult
from app.models.document import DocumentChunk
from app.models.financial import FinancialMetrics


@runtime_checkable
class AbstractAnalyzer(Protocol):
    """Structural protocol for all document analyzers."""

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        """Analyse the given document chunks and return a populated result.

        Parameters
        ----------
        request:
            The originating analysis request (includes type, prompt, options).
        chunks:
            The pre-processed text chunks from the converted document.
        metrics:
            Optional pre-computed financial metrics; provided only when the
            analysis type requires numerical context.

        Returns
        -------
        AnalysisResult
            Fully populated result. Must never be None. Use the ``warnings``
            field to record missing data rather than raising.
        """
        ...
