"""API request/response schemas for the analysis endpoints."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Input payload for POST /api/v1/analyze."""

    prompt: str = Field(..., min_length=1, description="User prompt describing the analysis needed")
    document_ids: list[UUID] = Field(default_factory=list, description="Optional document UUIDs")
    analysis_type: str | None = Field(default=None, description="Optional analysis type override (e.g. 'financial')")
    provider: str | None = Field(default=None, description="LLM provider: 'openai' or 'local'")
    model_id: str | None = Field(default=None, description="Model ID override (OpenAI model name or HuggingFace repo ID)")


class AnalyzeResponse(BaseModel):
    """Output payload returned by POST /api/v1/analyze."""

    request_id: UUID
    analysis_type: str
    summary: str
    narrative: str
    key_findings: list[str]
    recommendations: list[str]
    warnings: list[str]
    metrics: dict[str, float]
    model_used: str | None
