"""Pydantic schemas used by the API and the service layer."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# --------------------------------------------------------------------------- #
# Domain / LLM intermediate schemas
# --------------------------------------------------------------------------- #


class CuriosityScore(BaseModel):
    """Result of scoring an article for curiosity potential."""

    curiosity_score: float = Field(ge=0, le=10)
    hidden_mechanism_score: float = Field(ge=0, le=10)
    reason: str = ""


class RabbitHoleContent(BaseModel):
    """The structured content produced by the generation LLM call."""

    title: str
    observation: str
    question: str
    hidden_mechanism: str
    explanation: str
    interesting_fact: str
    why_it_matters: str
    follow_up_question: str
    category: str
    source_url: str = ""


# --------------------------------------------------------------------------- #
# API response schemas
# --------------------------------------------------------------------------- #


class RabbitHoleOut(BaseModel):
    """Full rabbit hole representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    observation: str
    question: str
    hidden_mechanism: str
    explanation: str
    interesting_fact: str
    why_it_matters: str
    follow_up_question: str
    category: str
    source_url: str
    curiosity_score: float
    hidden_mechanism_score: float
    created_at: datetime


class RabbitHoleSummary(BaseModel):
    """Condensed rabbit hole representation for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    observation: str
    question: str
    category: str
    curiosity_score: float
    hidden_mechanism_score: float
    source_url: str
    created_at: datetime


class FeedResponse(BaseModel):
    """Paginated daily feed payload."""

    count: int
    total: int
    generated_at: datetime
    items: list[RabbitHoleSummary]


class AskRequest(BaseModel):
    """User follow-up question about a rabbit hole."""

    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    answer: str
    provider: str


class CategoryCount(BaseModel):
    category: str
    count: int


class CategoriesResponse(BaseModel):
    categories: list[CategoryCount]


class SearchResult(RabbitHoleSummary):
    """A search hit, optionally annotated with a similarity distance."""

    distance: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[SearchResult]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    llm_provider: str
    embedding_provider: str
    database: str


# --------------------------------------------------------------------------- #
# Admin / operational schemas
# --------------------------------------------------------------------------- #


class PipelineCounters(BaseModel):
    ingested: int = 0
    scored: int = 0
    passed: int = 0
    rejected: int = 0
    generated: int = 0
    duplicates: int = 0
    failed: int = 0
    feed_size: int = 0


class PipelineRunState(BaseModel):
    running: bool
    stage: str
    stage_total: int
    stage_processed: int
    stage_elapsed_seconds: float
    stage_eta_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    run_elapsed_seconds: Optional[float] = None
    drain: bool
    counters: PipelineCounters
    errors: list[str] = Field(default_factory=list)


class ArticleStatusCounts(BaseModel):
    new: int = 0
    scored: int = 0
    rejected: int = 0
    generated: int = 0
    duplicate: int = 0
    failed: int = 0


class AdminStatusResponse(BaseModel):
    """Everything the admin panel needs in a single payload."""

    app: str
    version: str
    llm_provider: str
    embedding_provider: str
    database: str
    daily_feed_size: int
    total_rabbit_holes: int
    feed_count: int
    articles: ArticleStatusCounts
    pipeline: PipelineRunState
