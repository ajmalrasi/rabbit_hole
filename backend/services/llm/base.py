"""Abstract interface that every LLM provider must implement."""
from __future__ import annotations

import abc


class LLMProvider(abc.ABC):
    """Common contract for text generation and embeddings.

    Implementations are responsible for talking to a specific backend (Ollama,
    OpenAI, Gemini, ...). The rest of the application depends only on this
    interface, which keeps the provider swappable via configuration.
    """

    name: str = "base"

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        """Return the model's text completion for ``prompt``.

        When ``json_mode`` is True the provider should request a JSON-only
        response from the model where supported.
        """

    @abc.abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for ``text``."""

    async def aclose(self) -> None:
        """Release any underlying resources (HTTP clients, etc.)."""
