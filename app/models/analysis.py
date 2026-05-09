"""Analysis-level Pydantic models.

AnalysisType    — enum of supported analysis modes.
AnalysisRequest — what the user asked for.
AnalysisResult  — fully populated output, never None.
"""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AnalysisType(StrEnum):
    """Supported analysis modes routed by app/routing/router.py."""

    SUMMARY = "summary"
    FINANCIAL = "financial"
    COMPARISON = "comparison"
    LEGAL = "legal"
    AUDIT = "audit"
    CUSTOM = "custom"


class AnalysisRequest(BaseModel):
    """Input to the analysis pipeline."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    analysis_type: AnalysisType = AnalysisType.SUMMARY
    prompt: str
    document_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    options: dict[str, str] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Output from an analyzer — always fully populated, never None."""

    model_config = ConfigDict(frozen=False)

    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    analysis_type: AnalysisType
    summary: str = ""
    narrative: str = ""
    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    model_used: str | None = None
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
