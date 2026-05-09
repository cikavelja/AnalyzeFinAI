"""AnalystAgent — specialist MAF agent for financial and document analysis.

Tools:
    run_financial_calculation  — calls the deterministic calculator engine
    analyze_document           — runs the appropriate analyzer for a document
"""
from __future__ import annotations

import json

import structlog
from agent_framework import Agent

from app.agents._client import make_agent_client
from app.config import settings
from app.exceptions import AnalysisError

logger = structlog.get_logger(__name__)# ---------------------------------------------------------------------------
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
        from uuid import UUID  # noqa: PLC0415

        from app.financial.calculator import calculate_metrics  # noqa: PLC0415
        from app.financial.extractor import extract_dataframe  # noqa: PLC0415
        from app.ingestion.document_loader import load_chunks  # noqa: PLC0415

        logger.info(
            "analyst_financial_calc",
            document_id=document_id,
            calculation_type=calculation_type,
        )

        chunks = await load_chunks([UUID(document_id)])
        df = extract_dataframe(chunks)
        if df.empty:
            return json.dumps({
                "warning": "No financial data could be extracted from the document.",
                "document_id": document_id,
            })
        metrics = calculate_metrics(df)
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

        from app.ingestion.document_loader import load_chunks  # noqa: PLC0415
        from app.models.analysis import AnalysisRequest, AnalysisType  # noqa: PLC0415

        try:
            atype = AnalysisType(analysis_type.lower())
        except ValueError:
            atype = AnalysisType.SUMMARY

        request = AnalysisRequest(
            analysis_type=atype,
            prompt=f"Analyse document {document_id}",
            document_ids=[UUID(document_id)],
        )

        chunks = await load_chunks([UUID(document_id)])

        if atype == AnalysisType.FINANCIAL:
            from app.analyzers.financial import FinancialAnalyzer  # noqa: PLC0415
            from app.financial.calculator import calculate_metrics  # noqa: PLC0415
            from app.financial.extractor import extract_dataframe  # noqa: PLC0415

            df = extract_dataframe(chunks)
            metrics = calculate_metrics(df) if not df.empty else None
            result = await FinancialAnalyzer().analyze(request, chunks=chunks, metrics=metrics)
        else:
            from app.analyzers.universal import UniversalAnalyzer  # noqa: PLC0415

            result = await UniversalAnalyzer().analyze(request, chunks=chunks)

        return result.model_dump_json()

    except Exception as exc:
        logger.error("analyst_analyze_document_failed", error=str(exc))
        return json.dumps({"error": str(exc), "status": "failed"})


# ---------------------------------------------------------------------------
# Agent — lazy singleton (constructed on first access, not at import time)
# ---------------------------------------------------------------------------

_analyst_agent: Agent | None = None


def _build_analyst_agent() -> Agent:
    if settings.local_only_mode:
        raise AnalysisError("LOCAL_ONLY_MODE is enabled — agent LLM calls are blocked.")
    return Agent(
        name="AnalystAgent",
        client=make_agent_client(),
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
