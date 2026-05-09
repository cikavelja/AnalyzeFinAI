"""SummaryAnalyzer — produces an executive summary of document chunks via LLM.

Follows the AbstractAnalyzer protocol. Emits AuditEvents at start and end.
LLM is used only for narrative generation — no arithmetic in this module.
"""
from __future__ import annotations

import structlog

from app.audit.logger import audit_logger
from app.llm.prompt_templates import get_system_prompt, get_user_prompt
from app.llm.provider import AbstractLLMProvider, OpenAIProvider
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisType
from app.models.audit import AuditEvent
from app.models.document import DocumentChunk
from app.models.financial import FinancialMetrics

logger = structlog.get_logger(__name__)


class SummaryAnalyzer:
    """Produces a concise executive summary using an LLM."""

    def __init__(self, llm_provider: AbstractLLMProvider | None = None) -> None:
        self.llm_provider: AbstractLLMProvider = llm_provider or OpenAIProvider()

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        """Summarise document chunks and return a populated AnalysisResult."""

        await audit_logger.emit(
            AuditEvent(
                event_type="analysis",
                request_id=request.id,
                status="started",
                detail=f"{self.__class__.__name__} started for request {request.id}",
            )
        )

        warnings: list[str] = []
        summary = ""
        narrative = ""

        try:
            if not chunks:
                warnings.append("No document chunks provided — summary will be empty.")
                summary = "No content available to summarise."
            else:
                context = "\n\n".join(chunk.text for chunk in chunks)
                system = get_system_prompt(AnalysisType.SUMMARY)
                user = get_user_prompt(AnalysisType.SUMMARY, context=context)
                summary = await self.llm_provider.complete(system, user)
                narrative = summary

        except Exception as exc:
            logger.error(
                "summary_analyzer_llm_error",
                request_id=str(request.id),
                error=str(exc),
            )
            warnings.append(f"LLM call failed: {exc}. Returning partial result.")
            summary = "Summary unavailable due to LLM error."

        result = AnalysisResult(
            request_id=request.id,
            analysis_type=AnalysisType.SUMMARY,
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
                detail=f"{self.__class__.__name__} completed",
                model_used=self.llm_provider.model_name,
            )
        )

        return result
