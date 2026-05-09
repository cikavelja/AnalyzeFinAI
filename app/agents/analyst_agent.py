"""AnalystAgent — specialist MAF agent for financial and document analysis.

Tools:
    run_financial_calculation  — calls the deterministic calculator engine
    analyze_document           — runs the appropriate analyzer for a document
"""
from __future__ import annotations

import json

import structlog
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from app.config import settings

logger = structlog.get_logger(__name__)


def _make_client() -> OpenAIChatClient:
    """Build OpenAIChatClient, omitting api_key when unset so the SDK reads OPENAI_API_KEY from env."""
    kwargs: dict = {"model": settings.openai_model}
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    return OpenAIChatClient(**kwargs)


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

async def run_financial_calculation(document_id: str, calculation_type: str) -> str:
    """
    Run a deterministic financial calculation on a converted document.

    Parameters
    ----------
    document_id : str
        UUID of the document whose data should be calculated.
    calculation_type : str
        One of: 'yoy', 'cagr', 'ratios', 'anomalies', 'trends'.

    Returns a JSON string of FinancialMetrics.
    """
    try:
        import pandas as pd  # noqa: PLC0415

        from app.financial.calculator import calculate_metrics  # noqa: PLC0415

        # In a full implementation this would load the document's extracted DataFrame.
        # For Phase 1 we return a stub indicating the document_id was received.
        logger.info(
            "analyst_financial_calc",
            document_id=document_id,
            calculation_type=calculation_type,
        )

        # Stub: create a minimal DataFrame to exercise the calculator
        stub_df = pd.DataFrame(
            {
                "revenue": [100_000.0, 110_000.0, 121_000.0],
                "cogs": [60_000.0, 65_000.0, 70_000.0],
            }
        )
        metrics = calculate_metrics(stub_df)
        return metrics.model_dump_json()

    except Exception as exc:
        logger.error("analyst_financial_calc_failed", error=str(exc))
        return json.dumps({"error": str(exc), "status": "failed"})


async def analyze_document(document_id: str, analysis_type: str) -> str:
    """
    Run the appropriate analyzer for a document and return the AnalysisResult.

    Parameters
    ----------
    document_id : str
        UUID of the document to analyse.
    analysis_type : str
        One of: 'summary', 'financial', 'comparison', 'legal', 'audit', 'custom'.

    Returns a JSON string of AnalysisResult.
    """
    try:
        from uuid import UUID  # noqa: PLC0415

        from app.analyzers.summary import SummaryAnalyzer  # noqa: PLC0415
        from app.models.analysis import AnalysisRequest, AnalysisType  # noqa: PLC0415

        # Resolve analysis type
        try:
            atype = AnalysisType(analysis_type.lower())
        except ValueError:
            atype = AnalysisType.SUMMARY

        request = AnalysisRequest(
            analysis_type=atype,
            prompt=f"Analyse document {document_id}",
            document_ids=[UUID(document_id)],
        )

        # For Phase 1, only SummaryAnalyzer is fully implemented
        if atype == AnalysisType.SUMMARY:
            analyzer = SummaryAnalyzer()
            result = await analyzer.analyze(request, chunks=[])
        else:
            from app.models.analysis import AnalysisResult  # noqa: PLC0415

            result = AnalysisResult(
                request_id=request.id,
                analysis_type=atype,
                summary=f"Analyzer for '{analysis_type}' not yet implemented.",
                warnings=[f"'{analysis_type}' analyzer is a stub in Phase 1."],
            )

        return result.model_dump_json()

    except Exception as exc:
        logger.error("analyst_analyze_document_failed", error=str(exc))
        return json.dumps({"error": str(exc), "status": "failed"})


# ---------------------------------------------------------------------------
# Agent — lazy singleton (constructed on first access, not at import time)
# ---------------------------------------------------------------------------

_analyst_agent: Agent | None = None


def _build_analyst_agent() -> Agent:
    return Agent(
        name="AnalystAgent",
        client=_make_client(),
        instructions=(
            "You are the AnalystAgent for AnalizerAI. "
            "You specialise in document analysis and financial calculations. "
            "Use run_financial_calculation for any numerical financial work. "
            "Use analyze_document to produce a structured AnalysisResult for any document. "
            "Always prefer deterministic tools over making up numbers. "
            "Return your findings as structured JSON."
        ),
        tools=[run_financial_calculation, analyze_document],
    )


def __getattr__(name: str) -> object:
    global _analyst_agent
    if name == "analyst_agent":
        if _analyst_agent is None:
            _analyst_agent = _build_analyst_agent()
        return _analyst_agent
    raise AttributeError(name)
