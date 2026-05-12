"""Prompt templates for each AnalysisType.

These templates are the only place where prompt strings are constructed.
No business logic lives here — only string building.
"""
from __future__ import annotations

from app.models.analysis import AnalysisType

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS: dict[AnalysisType, str] = {
    AnalysisType.SUMMARY: (
        "You are a precise document analyst. Produce a concise executive summary "
        "that captures the key topics, conclusions, and important data points. "
        "Be factual. Do not hallucinate numbers — only cite figures present in the text."
    ),
    AnalysisType.FINANCIAL: (
        "You are a senior financial analyst. You will be given pre-computed financial "
        "metrics and the raw document text. Your task is to write a clear, professional "
        "narrative that explains the metrics in business context. "
        "Never invent or recalculate numbers — use only those provided."
    ),
    AnalysisType.COMPARISON: (
        "You are a comparative analysis specialist. Compare the documents or data "
        "sets provided, highlighting material differences, trends, and notable changes. "
        "Structure your response with clear headings."
    ),
    AnalysisType.LEGAL: (
        "You are a legal document reviewer. Identify key obligations, risk clauses, "
        "termination conditions, and any unusual or potentially problematic provisions. "
        "Flag anything that warrants legal counsel review."
    ),
    AnalysisType.AUDIT: (
        "You are an internal audit specialist. Review the provided content for "
        "compliance gaps, control weaknesses, and policy deviations. "
        "Prioritise findings by severity: Critical, High, Medium, Low."
    ),
    AnalysisType.CUSTOM: (
        "You are a versatile document analyst. Follow the user's specific instructions "
        "precisely. Be concise, accurate, and well-structured."
    ),
}

_DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful document analysis assistant. Analyse the provided content "
    "and respond clearly and accurately."
)


# ---------------------------------------------------------------------------
# User prompts
# ---------------------------------------------------------------------------

_USER_PROMPT_TEMPLATES: dict[AnalysisType, str] = {
    AnalysisType.SUMMARY: (
        "Please summarise the following document content:\n\n{context}"
    ),
    AnalysisType.FINANCIAL: (
        "Pre-computed metrics:\n{metrics}\n\n"
        "Document content:\n{context}\n\n"
        "Write a financial narrative explaining these results."
    ),
    AnalysisType.COMPARISON: (
        "Compare the following documents or datasets:\n\n{context}"
    ),
    AnalysisType.LEGAL: (
        "Review the following legal document:\n\n{context}"
    ),
    AnalysisType.AUDIT: (
        "Perform an audit review of the following content:\n\n{context}"
    ),
    AnalysisType.CUSTOM: (
        "{context}"
    ),
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_system_prompt(analysis_type: AnalysisType) -> str:
    """Return the system prompt for the given *analysis_type*."""
    return _SYSTEM_PROMPTS.get(analysis_type, _DEFAULT_SYSTEM_PROMPT)


def get_user_prompt(analysis_type: AnalysisType, context: str, metrics: str = "") -> str:
    """Render the user prompt template for *analysis_type*.

    Parameters
    ----------
    analysis_type:
        Which analysis mode is being executed.
    context:
        The document text / chunks joined as a single string.
    metrics:
        Optional pre-computed metrics JSON (used for FINANCIAL type).
    """
    if analysis_type == AnalysisType.FINANCIAL and metrics.strip() in ("", "{}"):
        # Metric extraction yielded nothing — instruct the LLM to work from the raw text.
        return (
            "Note: Automated metric extraction did not produce any pre-computed figures.\n\n"
            f"Document content:\n{context}\n\n"
            "Analyse the financial data visible in the document text above. "
            "Cite figures exactly as they appear — do not invent or recalculate numbers."
        )

    template = _USER_PROMPT_TEMPLATES.get(analysis_type, "{context}")
    return template.format(context=context, metrics=metrics)
