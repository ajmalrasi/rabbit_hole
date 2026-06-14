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
    generated_at: datetime
    items: list[RabbitHoleSummary]


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
