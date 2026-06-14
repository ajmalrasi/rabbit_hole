"""Ollama provider - runs local models, ideal for the Jetson Orin Nano."""
from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.logging_config import get_logger
from services.llm.base import LLMProvider

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        embedding_model: str,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._embedding_model = embedding_model
        self._client = httpx.AsyncClient(timeout=timeout)

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
        payload: dict = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"
            # Qwen3 thinking models emit structured output in ``thinking`` unless
            # disabled; turn off chain-of-thought for JSON scoring/generation.
            payload["think"] = False

        resp = await self._client.post(f"{self._base_url}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("response") or data.get("thinking") or "").strip()
        return text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed(self, text: str) -> list[float]:
        resp = await self._client.post(
            f"{self._base_url}/api/embeddings",
            json={"model": self._embedding_model, "prompt": text},
        )
        resp.raise_for_status()
        data = resp.json()
        embedding = data.get("embedding")
        if not embedding:
            raise ValueError("Ollama returned an empty embedding")
        return [float(x) for x in embedding]

    async def aclose(self) -> None:
        await self._client.aclose()
