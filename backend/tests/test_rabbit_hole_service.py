"""Tests for rabbit hole generation, dedup, and category normalisation."""
from __future__ import annotations

import json

from models.article import ArticleStatus
from services.embedding_service import EmbeddingService
from services.rabbit_hole_service import RabbitHoleService, _normalise_category
from tests.conftest import FakeLLMProvider, FakeRabbitHoleRepo


def test_normalise_category_canonical():
    assert _normalise_category("Physics") == "physics"
    assert _normalise_category("sports science") == "sports science"


def test_normalise_category_synonyms():
    assert _normalise_category("technology") == "engineering"
    assert _normalise_category("finance") == "economics"
    assert _normalise_category("geology") == "earth science"


def test_normalise_category_unknown_falls_back():
    assert _normalise_category("zzz unknown") == "other"


def _build_service(settings, repo, llm, embedding):
    embed_provider = FakeLLMProvider(embedding=embedding)
    embedding_service = EmbeddingService(embed_provider, repo, settings)
    return RabbitHoleService(llm, embedding_service, repo, settings)


async def test_generate_creates_rabbit_hole(settings, article, rabbit_hole_json):
    repo = FakeRabbitHoleRepo()
    repo.set_nearest_distance(None)  # no existing items
    llm = FakeLLMProvider(generate_responses=[rabbit_hole_json])
    service = _build_service(settings, repo, llm, embedding=[0.1] * 768)

    article.curiosity_score = 9
    article.hidden_mechanism_score = 8
    result = await service.generate_for_article(article)

    assert result is not None
    assert result.title == "Thin Air, Faster Balls"
    assert result.category == "sports science"
    assert result.curiosity_score == 9
    assert article.status == ArticleStatus.GENERATED
    assert len(repo.items) == 1


async def test_duplicate_is_rejected(settings, article, rabbit_hole_json):
    repo = FakeRabbitHoleRepo()
    repo.set_nearest_distance(0.05)  # below threshold -> duplicate
    llm = FakeLLMProvider(generate_responses=[rabbit_hole_json])
    service = _build_service(settings, repo, llm, embedding=[0.1] * 768)

    result = await service.generate_for_article(article)

    assert result is None
    assert article.status == ArticleStatus.DUPLICATE
    assert len(repo.items) == 0


async def test_missing_fields_marks_failed(settings, article):
    repo = FakeRabbitHoleRepo()
    incomplete = json.dumps({"title": "Only a title"})
    llm = FakeLLMProvider(generate_responses=[incomplete])
    service = _build_service(settings, repo, llm, embedding=[0.1] * 768)

    result = await service.generate_for_article(article)

    assert result is None
    assert article.status == ArticleStatus.FAILED
