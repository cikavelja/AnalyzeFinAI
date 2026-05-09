"""Keyword-based prompt router.

Routes a free-text user prompt to an ``AnalysisType`` without any LLM call.
The mapping is deterministic and fully testable.

Usage::

    from app.routing.router import route
    analysis_type = route("show me the financial summary and profit margins")
    # → AnalysisType.FINANCIAL
"""
from __future__ import annotations

import asyncio

import structlog

from app.audit.logger import audit_logger
from app.models.analysis import AnalysisType
from app.models.audit import AuditEvent

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Keyword → AnalysisType mappings
# Higher-priority types should appear first in the list.
# ---------------------------------------------------------------------------

_ROUTING_TABLE: list[tuple[AnalysisType, frozenset[str]]] = [
    (
        AnalysisType.FINANCIAL,
        frozenset(
            {
                "financial", "finance", "revenue", "profit", "loss", "margin",
                "ebitda", "cash flow", "cashflow", "balance sheet", "income statement",
                "p&l", "cost", "cogs", "gross", "net income", "earnings", "yoy",
                "year over year", "cagr", "growth", "liquidity", "ratio", "kpi",
            }
        ),
    ),
    (
        AnalysisType.LEGAL,
        frozenset(
            {
                "legal", "contract", "clause", "liability", "indemnity", "termination",
                "agreement", "obligation", "penalty", "compliance", "regulatory",
                "jurisdiction", "dispute", "warranty", "representation",
            }
        ),
    ),
    (
        AnalysisType.AUDIT,
        frozenset(
            {
                "audit", "internal audit", "control", "risk", "gap", "finding",
                "policy", "procedure", "sox", "internal control", "weakness",
                "remediation", "compliance audit",
            }
        ),
    ),
    (
        AnalysisType.COMPARISON,
        frozenset(
            {
                "compare", "comparison", "versus", "vs", "difference", "contrast",
                "benchmark", "against", "side by side", "relative to",
            }
        ),
    ),
]

_DEFAULT_TYPE = AnalysisType.SUMMARY


def route(prompt: str) -> AnalysisType:
    """Map *prompt* to the most appropriate ``AnalysisType``.

    The algorithm:
    1. Normalise the prompt to lower-case.
    2. Iterate ``_ROUTING_TABLE`` in priority order.
    3. Return the first type whose keyword set has any overlap with the prompt.
    4. Fall back to ``AnalysisType.SUMMARY`` when nothing matches.

    Parameters
    ----------
    prompt:
        Raw user input string.

    Returns
    -------
    AnalysisType
        The detected analysis type.
    """
    if not prompt or not prompt.strip():
        logger.debug("router_empty_prompt", fallback=_DEFAULT_TYPE)
        return _DEFAULT_TYPE

    normalised = prompt.lower()

    for analysis_type, keywords in _ROUTING_TABLE:
        if any(keyword in normalised for keyword in keywords):
            logger.debug(
                "router_matched",
                analysis_type=analysis_type,
                prompt_prefix=normalised[:80],
            )
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(audit_logger.emit(AuditEvent(
                    event_type="routing",
                    status="matched",
                    detail=f"Routed to {analysis_type}",
                )))
            except RuntimeError:
                pass
            return analysis_type

    logger.debug("router_no_match", fallback=_DEFAULT_TYPE)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(audit_logger.emit(AuditEvent(
            event_type="routing",
            status="fallback",
            detail=f"No match; defaulted to {_DEFAULT_TYPE}",
        )))
    except RuntimeError:
        pass
    return _DEFAULT_TYPE
