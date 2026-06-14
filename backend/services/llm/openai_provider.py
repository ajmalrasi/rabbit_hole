"""OpenAI-compatible provider.

Works with the official OpenAI API and any service that implements the same
``/chat/completions`` and ``/embeddings`` contract (LM Studio, vLLM, LiteLLM,
Together, and Google's Gemini OpenAI-compatible endpoint).
"""
from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.logging_config import get_logger
from services.llm.base import LLMProvider

logger = get_logger(__name__)


class OpenAICompatibleProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        embedding_model: str,
        timeout: float = 120.0,
        name: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._embedding_model = embedding_model
        if name:
            self.name = name
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = await self._client.post(
            f"{self._base_url}/chat/completions", json=payload
        )
        resp.raise_for_status()
        data = resp.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed(self, text: str) -> list[float]:
        resp = await self._client.post(
            f"{self._base_url}/embeddings",
            json={"model": self._embedding_model, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        embedding = data["data"][0]["embedding"]
        return [float(x) for x in embedding]

    async def aclose(self) -> None:
        await self._client.aclose()
