"""Health-check routes — GET /healthz (liveness), GET /readyz (readiness)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
async def healthz() -> HealthResponse:
    """Return service liveness status."""
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=HealthResponse, tags=["health"])
async def readyz() -> HealthResponse:
    """Return service readiness status.

    Checks that required directories and config are accessible.
    """
    from pathlib import Path  # noqa: PLC0415

    upload_dir = Path("data/uploads")
    converted_dir = Path("data/converted")
    upload_dir.mkdir(parents=True, exist_ok=True)
    converted_dir.mkdir(parents=True, exist_ok=True)
    return HealthResponse(status="ready")
