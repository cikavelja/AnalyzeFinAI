"""AnalysisResult validator — checks completeness before delivery."""
from __future__ import annotations

import structlog

from app.exceptions import ValidationError
from app.models.analysis import AnalysisResult

logger = structlog.get_logger(__name__)

_MIN_SUMMARY_LENGTH = 10


def validate_result(result: AnalysisResult) -> list[str]:
    """Validate *result* and return a list of issue strings (empty = valid).

    Parameters
    ----------
    result:
        The AnalysisResult to validate.

    Returns
    -------
    list[str]
        Empty list if valid; list of human-readable issue descriptions otherwise.

    Raises
    ------
    ValidationError
        If *result* is None.
    """
    issues: list[str] = []

    if result is None:
        raise ValidationError("result must not be None")

    if not result.summary:
        issues.append("Summary is empty.")
    elif len(result.summary) < _MIN_SUMMARY_LENGTH:
        issues.append(
            f"Summary too short ({len(result.summary)} chars; min {_MIN_SUMMARY_LENGTH})."
        )

    if not result.request_id:
        issues.append("request_id is missing.")

    if not result.analysis_type:
        issues.append("analysis_type is missing.")

    if issues:
        logger.warning("validation_failed", issues=issues)
    else:
        logger.debug("validation_passed", result_id=str(result.id))

    return issues
