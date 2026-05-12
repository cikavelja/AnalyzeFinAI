"""LLM provider abstractions.

AbstractLLMProvider   — structural Protocol that all providers must satisfy.
OpenAIProvider        — production OpenAI implementation using httpx.
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

import httpx
import structlog

from app.config import settings
from app.exceptions import AnalysisError

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class AbstractLLMProvider(Protocol):
    """Structural protocol for LLM providers."""

    model_name: str

    async def complete(self, system: str, user: str) -> str:
        """Return the full completion as a string."""
        ...

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Yield completion tokens one at a time."""
        ...


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------

class OpenAIProvider:
    """Chat-completion provider backed by the OpenAI API."""

    _BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.model_name: str = model or settings.openai_model
        self._api_key = api_key or settings.openai_api_key
        if not self._api_key:
            logger.warning("openai_api_key_not_set")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self, system: str, user: str, *, stream: bool = False
    ) -> dict[str, object]:
        return {
            "model": self.model_name,
            "stream": stream,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

    async def complete(self, system: str, user: str) -> str:
        """Return the full completion as a string.

        Raises:
            AnalysisError: if the API call fails.
        """
        if settings.local_only_mode:
            raise AnalysisError("LOCAL_ONLY_MODE is enabled — LLM calls are blocked.")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    self._BASE_URL,
                    headers=self._headers(),
                    json=self._build_payload(system, user),
                )
                resp.raise_for_status()
                data = resp.json()
                try:
                    return str(data["choices"][0]["message"]["content"])
                except (KeyError, IndexError, TypeError) as exc:
                    raise AnalysisError(
                        f"Unexpected OpenAI response format: {exc}. Body: {data}"
                    ) from exc
        except httpx.HTTPError as exc:
            logger.error("openai_http_error", error=str(exc))
            raise AnalysisError(f"OpenAI API error: {exc}") from exc

    async def stream(self, system: str, user: str) -> AsyncIterator[str]:
        """Yield completion tokens one at a time (server-sent events).

        Raises:
            AnalysisError: if the API call fails.
        """
        if settings.local_only_mode:
            raise AnalysisError("LOCAL_ONLY_MODE is enabled — LLM calls are blocked.")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    self._BASE_URL,
                    headers=self._headers(),
                    json=self._build_payload(system, user, stream=True),
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        try:
                            delta = chunk["choices"][0]["delta"].get("content", "")
                        except (KeyError, IndexError, TypeError):
                            continue
                        if delta:
                            yield delta
        except httpx.HTTPError as exc:
            logger.error("openai_stream_error", error=str(exc))
            raise AnalysisError(f"OpenAI stream error: {exc}") from exc
