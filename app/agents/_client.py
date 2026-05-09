"""Shared OpenAIChatClient factory for all MAF agents."""
from __future__ import annotations

from agent_framework.openai import OpenAIChatClient

from app.config import settings


def make_agent_client() -> OpenAIChatClient:
    """Build an OpenAIChatClient, omitting api_key when unset so the SDK reads OPENAI_API_KEY from env."""
    kwargs: dict = {"model": settings.openai_model}
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    return OpenAIChatClient(**kwargs)
