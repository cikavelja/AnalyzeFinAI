"""ReviewerAgent — specialist MAF agent that validates AnalysisResult completeness.

Tools:
    validate_analysis_result  — checks result completeness and returns a review report
"""
from __future__ import annotations

import json

import structlog
from agent_framework import Agent

from app.agents._client import make_agent_client
from app.config import settings
from app.exceptions import AnalysisError

logger = structlog.get_logger(__name__)# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = ("summary", "analysis_type", "request_id")
_MIN_SUMMARY_LENGTH = 10  # characters — matches app/validation/validator.py


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

async def validate_analysis_result(result_json: str) -> str:
    """
    Validate an AnalysisResult for completeness and return a structured review report.

    Checks performed:
    - All required fields are present and non-empty.
    - Summary is at least 10 characters long.
    - Warnings list is surfaced in the report.
    - Metrics dict is reported if present.

    Parameters
    ----------
    result_json : str
        JSON string of an AnalysisResult (from model_dump_json()).

    Returns a JSON string with keys: valid (bool), issues (list[str]),
    warnings (list[str]), metrics_count (int), summary (str).
    """
    try:
        data = json.loads(result_json)
    except json.JSONDecodeError as exc:
        logger.error("reviewer_json_parse_failed", error=str(exc))
        return json.dumps({"error": f"Invalid JSON: {exc}", "valid": False})

    issues: list[str] = []

    # Check required fields
    for field in _REQUIRED_FIELDS:
        value = data.get(field)
        if not value:
            issues.append(f"Required field '{field}' is missing or empty.")

    # Check summary length
    summary = data.get("summary", "")
    if isinstance(summary, str) and 0 < len(summary) < _MIN_SUMMARY_LENGTH:
        issues.append(
            f"Summary is too short ({len(summary)} chars; minimum {_MIN_SUMMARY_LENGTH})."
        )

    # Surface warnings from the result
    result_warnings: list[str] = data.get("warnings", [])

    metrics = data.get("metrics", {})
    metrics_count = len(metrics) if isinstance(metrics, dict) else 0

    valid = len(issues) == 0

    report = {
        "valid": valid,
        "issues": issues,
        "warnings": result_warnings,
        "metrics_count": metrics_count,
        "analysis_type": data.get("analysis_type", "unknown"),
        "summary_length": len(summary) if isinstance(summary, str) else 0,
    }

    logger.info(
        "reviewer_validation_complete",
        valid=valid,
        issues_count=len(issues),
    )

    return json.dumps(report)


# ---------------------------------------------------------------------------
# Agent — lazy singleton
# ---------------------------------------------------------------------------

_reviewer_agent: Agent | None = None


def _build_reviewer_agent() -> Agent:
    if settings.local_only_mode:
        raise AnalysisError("LOCAL_ONLY_MODE is enabled — agent LLM calls are blocked.")
    return Agent(
        name="ReviewerAgent",
        client=make_agent_client(),
        instructions=(
            "You are the ReviewerAgent for AnalizerAI. "
            "Your role is to quality-check analysis results before they are delivered to users. "
            "Use validate_analysis_result to check every AnalysisResult for completeness. "
            "If the result is invalid, clearly describe what is missing. "
            "If the result is valid, confirm it and provide a brief quality summary. "
            "Be precise and professional. Never approve an incomplete result."
        ),
        tools=[validate_analysis_result],
    )


def __getattr__(name: str) -> object:
    global _reviewer_agent
    if name == "reviewer_agent":
        if _reviewer_agent is None:
            _reviewer_agent = _build_reviewer_agent()
        return _reviewer_agent
    raise AttributeError(name)
