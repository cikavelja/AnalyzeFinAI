"""LocalHuggingFaceProvider — on-device LLM via HuggingFace transformers.

Requires the ``[local]`` optional dependencies:
    pip install "analizer-ai[local]"

Models are downloaded from HuggingFace Hub and cached in ``settings.hf_cache_dir``.
The loaded pipeline is cached in a module-level dict to avoid reloading on every request.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import AsyncIterator

import structlog

from app.config import settings
from app.exceptions import AnalysisError

logger = structlog.get_logger(__name__)

# Module-level pipeline cache: model_id → transformers pipeline object
_pipeline_cache: dict[str, object] = {}


def _local_model_path(model_id: str, cache_dir: str) -> str | None:
    """Return the local directory path if the model has already been downloaded."""
    safe_id = model_id.replace("/", "--")
    p = Path(cache_dir) / safe_id
    if p.is_dir() and any(p.iterdir()):
        return str(p)
    return None


# On CPU, 1024 tokens at ~1–3 tok/s = 5–17 minutes. Use 512 as a safe cap.
# Override via LOCAL_MAX_NEW_TOKENS env var if you have a GPU and need longer outputs.
_MAX_NEW_TOKENS = int(os.getenv("LOCAL_MAX_NEW_TOKENS", "512"))


def _build_pipeline(model_id: str, hf_token: str | None, cache_dir: str) -> object:
    """Load a text-generation pipeline (runs in a thread pool).

    Loads from the local cache directory when the model has been pre-downloaded,
    otherwise falls back to downloading from HuggingFace Hub.
    Do NOT pass cache_dir to hf_pipeline() — in transformers ≥5.x it leaks into
    model_kwargs and causes an error when calling generate().
    """
    try:
        import torch
        from transformers import pipeline as hf_pipeline
    except ImportError as exc:
        raise AnalysisError(
            "Local model support requires the [local] extras: "
            "pip install 'analizer-ai[local]'"
        ) from exc

    device_map = "auto" if torch.cuda.is_available() else "cpu"

    # Prefer loading from the local path so we never need cache_dir at inference time.
    local_path = _local_model_path(model_id, cache_dir)
    model_arg = local_path or model_id
    # Token only needed when fetching from HF Hub (not for local paths).
    token: str | bool = (hf_token if hf_token else False) if not local_path else False

    logger.info("loading_local_model", model_id=model_id, source=model_arg, device_map=device_map)
    pipe = hf_pipeline(
        "text-generation",
        model=model_arg,
        token=token,
        device_map=device_map,
        trust_remote_code=False,
    )
    logger.info("local_model_loaded", model_id=model_id)
    return pipe


async def _get_pipeline(model_id: str, hf_token: str | None, cache_dir: str) -> object:
    """Return cached pipeline, loading it on first call."""
    if model_id not in _pipeline_cache:
        _pipeline_cache[model_id] = await asyncio.to_thread(
            _build_pipeline, model_id, hf_token, cache_dir
        )
    return _pipeline_cache[model_id]


def _messages_to_prompt(system: str, user: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


class LocalHuggingFaceProvider:
    """Text-generation provider backed by a local HuggingFace model."""

    def __init__(
        self,
        model_id: str | None = None,
        hf_token: str | None = None,
        cache_dir: str | None = None,
    ) -> None:
        self.model_name: str = model_id or settings.local_model_id
        self._hf_token: str | None = hf_token or settings.hf_token or None
        self._cache_dir: str = cache_dir or settings.hf_cache_dir

    async def complete(self, system: str, user: str) -> str:
        """Return the full completion as a string.

        Raises:
            AnalysisError: if the model is not available or generation fails.
        """
        try:
            pipe = await _get_pipeline(self.model_name, self._hf_token, self._cache_dir)
            messages = _messages_to_prompt(system, user)

            def _generate() -> str:
                # Pass only max_new_tokens; do_sample is not passed to avoid the
                # "generation_config + explicit kwargs" deprecation warning in transformers ≥5.x.
                result = pipe(messages, max_new_tokens=_MAX_NEW_TOKENS)
                generated = result[0]["generated_text"]
                # Chat-template pipelines return the full conversation; take last turn.
                if isinstance(generated, list):
                    return str(generated[-1].get("content", ""))
                return str(generated)

            return await asyncio.to_thread(_generate)
        except AnalysisError:
            raise
        except Exception as exc:
            logger.error("local_provider_complete_error", model=self.model_name, error=str(exc))
            raise AnalysisError(f"Local model error: {exc}") from exc

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Yield completion tokens one at a time via TextIteratorStreamer.

        Raises:
            AnalysisError: if the model is not available or generation fails.
        """
        try:
            import threading

            from transformers import AutoTokenizer, TextIteratorStreamer
        except ImportError as exc:
            raise AnalysisError(
                "Local model support requires the [local] extras: "
                "pip install 'analizer-ai[local]'"
            ) from exc

        try:
            pipe = await _get_pipeline(self.model_name, self._hf_token, self._cache_dir)
            messages = _messages_to_prompt(system, user)

            # Load tokenizer from local path if available (avoids cache_dir kwarg issue).
            tokenizer_src = _local_model_path(self.model_name, self._cache_dir) or self.model_name
            token_arg: str | bool = (self._hf_token or False) if not _local_model_path(self.model_name, self._cache_dir) else False
            tokenizer: object = await asyncio.to_thread(
                AutoTokenizer.from_pretrained,
                tokenizer_src,
                token=token_arg,
            )
            streamer = TextIteratorStreamer(
                tokenizer,  # type: ignore[arg-type]
                skip_prompt=True,
                skip_special_tokens=True,
            )

            def _generate() -> None:
                pipe(messages, max_new_tokens=_MAX_NEW_TOKENS, streamer=streamer)

            thread = threading.Thread(target=_generate, daemon=True)
            thread.start()

            loop = asyncio.get_running_loop()
            try:
                for token_text in streamer:
                    if token_text:
                        yield token_text
                        await asyncio.sleep(0)  # yield control back to event loop
            finally:
                await loop.run_in_executor(None, thread.join)

        except AnalysisError:
            raise
        except Exception as exc:
            logger.error("local_provider_stream_error", model=self.model_name, error=str(exc))
            raise AnalysisError(f"Local model stream error: {exc}") from exc
