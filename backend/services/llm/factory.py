"""Factory functions that build LLM providers from configuration.

Providers are cached so the whole application shares a single HTTP client per
provider type. ``get_llm_provider`` returns the text-generation provider while
``get_embedding_provider`` returns the embeddings provider; they may differ
(e.g. local Ollama embeddings + remote OpenAI generation).
"""
from __future__ import annotations

from functools import lru_cache

from app.config import ProviderName, Settings, get_settings
from app.logging_config import get_logger
from services.llm.base import LLMProvider
from services.llm.gemini_provider import GeminiProvider
from services.llm.ollama_provider import OllamaProvider
from services.llm.openai_provider import OpenAICompatibleProvider

logger = get_logger(__name__)


def _build_provider(provider: ProviderName, settings: Settings) -> LLMProvider:
    if provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            embedding_model=settings.ollama_embedding_model,
            timeout=settings.http_timeout,
        )
    if provider == "openai":
        return OpenAICompatibleProvider(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            embedding_model=settings.openai_embedding_model,
            timeout=settings.http_timeout,
        )
    if provider == "gemini":
        return GeminiProvider(
            base_url=settings.gemini_base_url,
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            embedding_model=settings.gemini_embedding_model,
            timeout=settings.http_timeout,
        )
    raise ValueError(f"Unknown provider: {provider}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    logger.info("Initialising text LLM provider: %s", settings.llm_provider)
    return _build_provider(settings.llm_provider, settings)


@lru_cache
def get_embedding_provider() -> LLMProvider:
    settings = get_settings()
    logger.info("Initialising embedding provider: %s", settings.embedding_provider)
    return _build_provider(settings.embedding_provider, settings)


@lru_cache
def get_chat_provider() -> LLMProvider:
    """Provider for follow-up Q&A — prefers OpenAI (ChatGPT) when configured."""
    settings = get_settings()
    if settings.openai_api_key:
        logger.info("Initialising chat provider: openai (%s)", settings.openai_model)
        return _build_provider("openai", settings)
    logger.info(
        "OpenAI key not set; chat provider falls back to %s", settings.llm_provider
    )
    return get_llm_provider()


async def close_providers() -> None:
    """Close cached providers on application shutdown."""
    for getter in (get_llm_provider, get_embedding_provider, get_chat_provider):
        try:
            provider = getter()
        except Exception:  # pragma: no cover - defensive
            continue
        await provider.aclose()
    get_llm_provider.cache_clear()
    get_embedding_provider.cache_clear()
    get_chat_provider.cache_clear()
