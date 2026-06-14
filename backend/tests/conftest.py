"""Shared pytest fixtures and test doubles.

The tests exercise the service/business-logic layer in isolation using fakes,
so the suite runs without Postgres, pgvector, or a live LLM backend.
"""
from __future__ import annotations

import json

import pytest

from app.config import Settings
from models.article import Article, ArticleStatus
from models.rabbit_hole import RabbitHole
from services.llm.base import LLMProvider


class FakeLLMProvider(LLMProvider):
    """Deterministic LLM stand-in.

    ``generate_responses`` is a queue of strings returned in order; ``embedding``
    is the vector returned for every ``embed`` call.
    """

    name = "fake"

    def __init__(
        self,
        generate_responses: list[str] | None = None,
        embedding: list[float] | None = None,
    ) -> None:
        self._responses = list(generate_responses or [])
        self._embedding = embedding or [0.0] * 768
        self.generate_calls: list[str] = []
        self.embed_calls: list[str] = []

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str:
        self.generate_calls.append(prompt)
        if self._responses:
            return self._responses.pop(0)
        return "{}"

    async def embed(self, text: str) -> list[float]:
        self.embed_calls.append(text)
        return list(self._embedding)


class FakeRabbitHoleRepo:
    """In-memory stand-in for RabbitHoleRepository."""

    def __init__(self) -> None:
        self.items: list[RabbitHole] = []
        self._nearest: float | None = None
        self.committed = False

    def set_nearest_distance(self, value: float | None) -> None:
        self._nearest = value

    def nearest_distance(self, embedding: list[float]) -> float | None:
        return self._nearest

    def add(self, obj: RabbitHole) -> RabbitHole:
        obj.id = len(self.items) + 1
        self.items.append(obj)
        return obj

    def top_candidates(self, limit: int = 100) -> list[RabbitHole]:
        return sorted(
            self.items,
            key=lambda r: (r.curiosity_score + r.hidden_mechanism_score),
            reverse=True,
        )[:limit]

    def list_feed(self, limit: int = 20, offset: int = 0):
        feed = [r for r in self.items if r.in_feed]
        feed.sort(key=lambda r: r.feed_rank or 0)
        return feed[offset : offset + limit]

    def clear_feed(self) -> None:
        for r in self.items:
            r.in_feed = False
            r.feed_rank = None

    def commit(self) -> None:
        self.committed = True


@pytest.fixture
def settings() -> Settings:
    return Settings(
        min_curiosity_score=6.0,
        min_hidden_mechanism_score=6.0,
        dedup_distance_threshold=0.15,
        embedding_dim=768,
        daily_feed_size=3,
    )


@pytest.fixture
def article() -> Article:
    return Article(
        guid="guid-1",
        source="Test",
        title="Why do football matches at high altitude behave differently?",
        url="https://example.com/altitude",
        summary="A look at matches played in thin mountain air.",
        status=ArticleStatus.NEW,
    )


def make_rabbit_hole_content() -> dict:
    return {
        "title": "Thin Air, Faster Balls",
        "observation": "Footballs fly farther in mountain stadiums.",
        "question": "What invisible system causes this?",
        "hidden_mechanism": "Reduced air density lowers aerodynamic drag.",
        "explanation": "At altitude the atmosphere is thinner, so drag drops.",
        "interesting_fact": "Air density at 2500m is ~25% lower than at sea level.",
        "why_it_matters": "It changes player tactics and ball control.",
        "follow_up_question": "How do players recalibrate their passing?",
        "category": "sports science",
        "source_url": "https://example.com/altitude",
    }


@pytest.fixture
def rabbit_hole_json() -> str:
    return json.dumps(make_rabbit_hole_content())
