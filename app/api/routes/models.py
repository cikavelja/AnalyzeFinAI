"""Model management routes.

GET  /api/v1/models                  — list presets and their download status
POST /api/v1/models/download         — trigger async download of a model
GET  /api/v1/models/{encoded_id}/status — poll download status for a model
"""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

import structlog
from fastapi import APIRouter

from app.api.schemas.models import (
    DownloadRequest,
    ModelPreset,
    ModelStatusResponse,
    ModelsListResponse,
)
from app.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/models", tags=["models"])

# ---------------------------------------------------------------------------
# Preset catalogue
# ---------------------------------------------------------------------------

PRESET_MODELS: list[ModelPreset] = [
    ModelPreset(
        model_id="microsoft/Phi-3.5-mini-instruct",
        name="Phi-3.5 Mini",
        family="phi",
        description="Microsoft Phi-3.5 Mini — 3.8 B params, instruction-tuned, runs on CPU",
        size_hint="~7 GB",
        requires_token=False,
    ),
    ModelPreset(
        model_id="meta-llama/Llama-3.2-1B-Instruct",
        name="Llama 3.2 1B",
        family="llama",
        description="Meta Llama 3.2 — 1 B params, instruction-tuned, very lightweight",
        size_hint="~2.5 GB",
        requires_token=True,
    ),
    ModelPreset(
        model_id="google/gemma-2-2b-it",
        name="Gemma 2 2B",
        family="gemma",
        description="Google Gemma 2 — 2 B params, instruction-tuned",
        size_hint="~5 GB",
        requires_token=True,
    ),
]

_PRESET_IDS = {m.model_id for m in PRESET_MODELS}

# ---------------------------------------------------------------------------
# In-memory download state  model_id → ModelStatusResponse
# ---------------------------------------------------------------------------

_download_state: dict[str, ModelStatusResponse] = {}


def _cache_path(model_id: str) -> Path:
    """Local directory where the model would be stored."""
    safe_id = model_id.replace("/", "--")
    return Path(settings.hf_cache_dir) / safe_id


def _is_ready(model_id: str) -> bool:
    """Check if model files already exist on disk."""
    p = _cache_path(model_id)
    return p.is_dir() and any(p.iterdir())


def _current_status(model_id: str) -> ModelStatusResponse:
    if model_id in _download_state:
        return _download_state[model_id]
    if _is_ready(model_id):
        return ModelStatusResponse(model_id=model_id, status="ready", progress_pct=100.0)
    return ModelStatusResponse(model_id=model_id, status="not_downloaded")


# ---------------------------------------------------------------------------
# Background download task
# ---------------------------------------------------------------------------

def _sync_download(model_id: str, hf_token: str | None, cache_dir: str) -> None:
    """Blocking download — runs in a thread pool executor."""
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=model_id,
        token=hf_token or None,
        local_dir=str(_cache_path(model_id)),
        ignore_patterns=["*.msgpack", "flax_model*", "tf_model*", "rust_model*"],
    )


async def _download_model_task(model_id: str, hf_token: str | None) -> None:
    """Async wrapper that updates _download_state before/after download."""
    _download_state[model_id] = ModelStatusResponse(
        model_id=model_id, status="downloading", progress_pct=0.0
    )
    try:
        await asyncio.to_thread(
            _sync_download, model_id, hf_token, settings.hf_cache_dir
        )
        _download_state[model_id] = ModelStatusResponse(
            model_id=model_id, status="ready", progress_pct=100.0
        )
        logger.info("model_download_complete", model_id=model_id)
    except Exception as exc:
        logger.error("model_download_error", model_id=model_id, error=str(exc))
        _download_state[model_id] = ModelStatusResponse(
            model_id=model_id, status="error", error=str(exc)
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=ModelsListResponse)
async def list_models() -> ModelsListResponse:
    """Return all preset models and their current download status."""
    statuses = {m.model_id: _current_status(m.model_id) for m in PRESET_MODELS}
    return ModelsListResponse(presets=PRESET_MODELS, statuses=statuses)


@router.post("/download", response_model=ModelStatusResponse, status_code=202)
async def download_model(body: DownloadRequest) -> ModelStatusResponse:
    """Trigger an async download of a model.  Returns 202 Accepted immediately."""
    from fastapi import HTTPException

    model_id = body.model_id

    if model_id not in _PRESET_IDS:
        raise HTTPException(
            status_code=422,
            detail=f"model_id '{model_id}' is not in the approved preset list. "
                   f"Valid values: {sorted(_PRESET_IDS)}",
        )

    current = _current_status(model_id)

    if current.status in {"ready", "downloading"}:
        return current

    token = body.hf_token or (settings.hf_token or None)

    # Fire-and-forget background task
    asyncio.create_task(_download_model_task(model_id, token))

    _download_state[model_id] = ModelStatusResponse(
        model_id=model_id, status="downloading", progress_pct=0.0
    )
    logger.info("model_download_started", model_id=model_id)
    return _download_state[model_id]


@router.get("/{encoded_id}/status", response_model=ModelStatusResponse)
async def get_model_status(encoded_id: str) -> ModelStatusResponse:
    """Poll the download / readiness status for a single model.

    ``encoded_id`` uses ``--`` as separator instead of ``/`` to keep it URL-safe
    (e.g. ``microsoft--Phi-3.5-mini-instruct``).
    """
    model_id = encoded_id.replace("--", "/")
    return _current_status(model_id)


@router.delete("/{encoded_id}", response_model=ModelStatusResponse)
async def delete_model(encoded_id: str) -> ModelStatusResponse:
    """Delete a locally cached model from disk so it can be re-downloaded.

    ``encoded_id`` uses ``--`` as separator instead of ``/`` (e.g.
    ``microsoft--Phi-3.5-mini-instruct``).

    Returns the new status (``not_downloaded``) on success.
    Raises 409 if the model is currently being downloaded.
    """
    from fastapi import HTTPException

    model_id = encoded_id.replace("--", "/")
    current = _current_status(model_id)

    if current.status == "downloading":
        raise HTTPException(
            status_code=409,
            detail=f"Model '{model_id}' is currently downloading — wait for it to finish before deleting.",
        )

    cache = _cache_path(model_id)
    if cache.exists():
        await asyncio.to_thread(shutil.rmtree, cache, ignore_errors=True)
        logger.info("model_deleted", model_id=model_id, path=str(cache))

    # Also evict from the in-memory pipeline cache if loaded
    from app.llm.local_provider import _pipeline_cache
    _pipeline_cache.pop(model_id, None)

    # Clear download state so status reverts to not_downloaded
    _download_state.pop(model_id, None)

    logger.info("model_delete_complete", model_id=model_id)
    return _current_status(model_id)
