"""LLM provider factory.

Usage::

    from app.llm.factory import get_llm_provider

    provider = get_llm_provider(provider="local", model_id="microsoft/Phi-3.5-mini-instruct")
    result = await provider.complete(system, user)
"""
from __future__ import annotations

from app.config import settings
from app.llm.provider import AbstractLLMProvider, OpenAIProvider


def get_llm_provider(
    provider: str | None = None,
    model_id: str | None = None,
) -> AbstractLLMProvider:
    """Return the appropriate LLM provider.

    Parameters
    ----------
    provider:
        ``"openai"`` or ``"local"``. Falls back to ``settings.llm_provider``.
    model_id:
        For ``"local"``: the HuggingFace model ID to load.
        For ``"openai"``: the OpenAI model name (e.g. ``"gpt-4o"``).
        Falls back to the relevant setting when omitted.
    """
    effective_provider = (provider or settings.llm_provider).lower()

    if effective_provider == "local":
        from app.llm.local_provider import LocalHuggingFaceProvider

        return LocalHuggingFaceProvider(model_id=model_id)

    # Default: OpenAI
    return OpenAIProvider(model=model_id or None)
