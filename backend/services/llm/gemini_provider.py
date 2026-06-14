"""Gemini provider.

Google exposes an OpenAI-compatible surface at
``/v1beta/openai`` which lets us reuse the OpenAI-compatible client. This keeps
the provider matrix small while still treating Gemini as a first-class option.
"""
from __future__ import annotations

from services.llm.openai_provider import OpenAICompatibleProvider


class GeminiProvider(OpenAICompatibleProvider):
    """Thin specialisation of the OpenAI-compatible provider for Gemini."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        embedding_model: str,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            model=model,
            embedding_model=embedding_model,
            timeout=timeout,
            name="gemini",
        )
