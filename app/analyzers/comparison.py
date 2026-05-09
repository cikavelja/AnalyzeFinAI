"""Stub analyzers for Comparison, Audit, Legal, and Custom analysis types.

Each is a valid AbstractAnalyzer implementation that raises NotImplementedError
until fully implemented in a later phase.
"""
from __future__ import annotations

from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisType
from app.models.document import DocumentChunk
from app.models.financial import FinancialMetrics


class ComparisonAnalyzer:
    """Compares two or more documents. Not yet implemented."""

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        raise NotImplementedError("ComparisonAnalyzer is not yet implemented")


class AuditAnalyzer:
    """Performs audit review of document content. Not yet implemented."""

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        raise NotImplementedError("AuditAnalyzer is not yet implemented")


class LegalAnalyzer:
    """Reviews legal documents for risk clauses. Not yet implemented."""

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        raise NotImplementedError("LegalAnalyzer is not yet implemented")


class CustomAnalyzer:
    """Executes user-defined analysis instructions. Not yet implemented."""

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        raise NotImplementedError("CustomAnalyzer is not yet implemented")
