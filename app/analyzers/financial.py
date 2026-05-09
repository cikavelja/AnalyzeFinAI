"""FinancialAnalyzer — numerical metrics + LLM narrative.

Calls app/financial/calculator.py for all arithmetic, then passes the
pre-computed FinancialMetrics to the LLM for narrative generation.
"""
from __future__ import annotations

import structlog

from app.analyzers.base import LLM_UNAVAILABLE_NARRATIVE, LLM_UNAVAILABLE_SUMMARY
from app.audit.logger import audit_logger
from app.llm.prompt_templates import get_system_prompt, get_user_prompt
from app.llm.provider import AbstractLLMProvider, OpenAIProvider
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisType
from app.models.audit import AuditEvent
from app.models.document import DocumentChunk
from app.models.financial import FinancialMetrics

logger = structlog.get_logger(__name__)


class FinancialAnalyzer:
    """Combines deterministic metrics with LLM narrative for financial analysis."""

    def __init__(self, llm_provider: AbstractLLMProvider | None = None) -> None:
        self.llm_provider: AbstractLLMProvider = llm_provider or OpenAIProvider()

    async def analyze(
        self,
        request: AnalysisRequest,
        chunks: list[DocumentChunk],
        metrics: FinancialMetrics | None = None,
    ) -> AnalysisResult:
        """Generate financial analysis — metrics must be pre-computed and passed in."""

        await audit_logger.emit(
            AuditEvent(
                event_type="analysis",
                request_id=request.id,
                status="started",
                detail=f"{self.__class__.__name__} started",
            )
        )

        warnings: list[str] = []
        narrative = ""

        try:
            context = "\n\n".join(chunk.text for chunk in chunks) if chunks else ""
            metrics_json = metrics.model_dump_json() if metrics else "{}"

            if not chunks:
                warnings.append("No document chunks provided.")

            system = get_system_prompt(AnalysisType.FINANCIAL)
            user = get_user_prompt(
                AnalysisType.FINANCIAL, context=context, metrics=metrics_json
            )
            narrative = await self.llm_provider.complete(system, user)

        except Exception as exc:
            logger.error("financial_analyzer_error", error=str(exc))
            warnings.append(f"LLM call failed: {exc}")
            narrative = LLM_UNAVAILABLE_NARRATIVE

        metric_dict: dict[str, float] = {}
        if metrics:
            for field, val in metrics.model_dump().items():
                if isinstance(val, float | int) and val is not None:
                    metric_dict[field] = float(val)

        result = AnalysisResult(
            request_id=request.id,
            analysis_type=AnalysisType.FINANCIAL,
            summary=narrative[:500] if narrative and narrative != LLM_UNAVAILABLE_NARRATIVE else LLM_UNAVAILABLE_SUMMARY,
            narrative=narrative,
            metrics=metric_dict,
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
