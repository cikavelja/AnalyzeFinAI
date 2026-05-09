"""UniversalAnalyzer — single LLM-based analyzer for all non-financial analysis types.

Replaces the previous per-type stub classes (ComparisonAnalyzer, LegalAnalyzer,
AuditAnalyzer, CustomAnalyzer) and SummaryAnalyzer. The LLM selects the right
behaviour through the prompt template already defined for each AnalysisType.

FinancialAnalyzer is kept separate because it requires deterministic pre-computation
of metrics before any LLM call.
"""
from __future__ import annotations

import structlog

from app.analyzers.base import LLM_UNAVAILABLE_SUMMARY
from app.audit.logger import audit_logger
from app.llm.prompt_templates import get_system_prompt, get_user_prompt
from app.llm.provider import AbstractLLMProvider, OpenAIProvider
from app.models.analysis import AnalysisRequest, AnalysisResult
from app.models.audit import AuditEvent
from app.models.document import DocumentChunk
from app.models.financial import FinancialMetrics

logger = structlog.get_logger(__name__)


class UniversalAnalyzer:
    """Handles SUMMARY, COMPARISON, LEGAL, AUDIT, and CUSTOM via prompt templates."""

    def __init__(self, llm_provider: AbstractLLMProvider | None = None) -> None:
        self.llm_provider: AbstractLLMProvider = llm_provider or OpenAIProvider()

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        """Analyse chunks using the prompt template for request.analysis_type."""

        await audit_logger.emit(
            AuditEvent(
                event_type="analysis",
                request_id=request.id,
                status="started",
                detail=f"{self.__class__.__name__} started ({request.analysis_type})",
            )
        )

        warnings: list[str] = []
        narrative = ""
        summary = ""

        try:
            if not chunks:
                warnings.append("No document chunks provided — analysis will be empty.")
                summary = "No content available to analyse."
            else:
                context = "\n\n".join(chunk.text for chunk in chunks)
                system = get_system_prompt(request.analysis_type)
                user = get_user_prompt(request.analysis_type, context=context)
                narrative = await self.llm_provider.complete(system, user)
                summary = narrative

        except Exception as exc:
            logger.error(
                "universal_analyzer_llm_error",
                request_id=str(request.id),
                analysis_type=str(request.analysis_type),
                error=str(exc),
            )
            warnings.append(f"LLM call failed: {exc}. Returning partial result.")
            summary = LLM_UNAVAILABLE_SUMMARY

        result = AnalysisResult(
            request_id=request.id,
            analysis_type=request.analysis_type,
            summary=summary,
            narrative=narrative,
            warnings=warnings,
            model_used=self.llm_provider.model_name,
        )

        await audit_logger.emit(
            AuditEvent(
                event_type="analysis",
                request_id=request.id,
                status="completed",
                detail=f"{self.__class__.__name__} completed ({request.analysis_type})",
                model_used=self.llm_provider.model_name,
            )
        )

        return result
