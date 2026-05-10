"""API schemas for model management endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ModelPreset(BaseModel):
    """A pre-defined HuggingFace model the user can download with one click."""

    model_id: str
    name: str
    family: str  # "phi" | "llama" | "gemma" | "custom"
    description: str
    size_hint: str  # human-readable estimated size, e.g. "~7 GB"
    requires_token: bool = False


class ModelStatusResponse(BaseModel):
    """Download / readiness status for a single model."""

    model_id: str
    status: str  # "not_downloaded" | "downloading" | "ready" | "error"
    progress_pct: float = Field(default=0.0, ge=0, le=100)
    error: str | None = None


class DownloadRequest(BaseModel):
    """Request body for POST /api/v1/models/download."""

    model_id: str = Field(..., description="HuggingFace model ID, e.g. 'microsoft/Phi-3.5-mini-instruct'")
    hf_token: str | None = Field(default=None, description="HuggingFace token for gated models")


class ModelsListResponse(BaseModel):
    """Response for GET /api/v1/models."""

    presets: list[ModelPreset]
    statuses: dict[str, ModelStatusResponse]  # model_id → status
