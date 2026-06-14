"""Application configuration loaded from environment variables.

All settings are centralised here using ``pydantic-settings`` so the rest of the
codebase can depend on a single, validated ``Settings`` object.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["ollama", "openai", "gemini"]


class Settings(BaseSettings):
    """Strongly typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Application -----
    app_name: str = "Rabbit Hole"
    app_env: str = "production"
    log_level: str = "INFO"
    cors_origins: str = "*"

    # ----- Database -----
    postgres_user: str = "rabbit"
    postgres_password: str = "rabbit_secret_change_me"
    postgres_db: str = "rabbit_hole"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # ----- Provider selection -----
    llm_provider: ProviderName = "ollama"
    embedding_provider: ProviderName = "ollama"

    # ----- Ollama -----
    ollama_base_url: str = "http://192.168.3.30:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embedding_model: str = "nomic-embed-text"

    # ----- OpenAI (and OpenAI-compatible) -----
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # ----- Gemini -----
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # ----- Embeddings -----
    embedding_dim: int = 768
    dedup_distance_threshold: float = 0.15

    # ----- Curiosity gating -----
    min_curiosity_score: float = 6.0
    min_hidden_mechanism_score: float = 6.0

    # ----- Pipeline / scheduler -----
    # Hour (UTC) for the once-daily pipeline: ingest RSS → score → generate → feed.
    daily_pipeline_hour: int = 6
    daily_pipeline_minute: int = 0
    max_articles_per_run: int = 60
    # When True, /admin/pipeline/process loops until NEW and SCORED queues are empty.
    # Scheduled runs still use one batch per cycle to keep Jetson runs bounded.
    pipeline_drain_on_process: bool = True
    run_on_startup: bool = False
    daily_feed_size: int = 20

    # ----- RSS cache -----
    # Directory for on-disk feed cache. Set to "" to disable caching.
    # Inside Docker this maps to a volume mount so cache survives restarts.
    rss_cache_dir: str = "/tmp/rss_cache"
    # Age in minutes before a cached feed is considered stale.
    rss_cache_ttl_minutes: int = 60

    # HTTP timeout (seconds) for outbound LLM / RSS calls
    http_timeout: float = 120.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """SQLAlchemy connection string using the psycopg (v3) driver."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (single source of truth)."""
    return Settings()
