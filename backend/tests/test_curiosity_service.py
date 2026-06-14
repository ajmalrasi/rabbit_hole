"""Tests for the curiosity scoring + gating service."""
from __future__ import annotations

import json

from models.article import ArticleStatus
from services.curiosity_service import CuriosityService
from tests.conftest import FakeLLMProvider


async def test_high_score_passes_gate(settings, article):
    llm = FakeLLMProvider(
        generate_responses=[
            json.dumps(
                {
                    "curiosity_score": 9,
                    "hidden_mechanism_score": 8.5,
                    "reason": "air density and drag",
                }
            )
        ]
    )
    service = CuriosityService(llm, settings)

    passed = await service.score_and_gate(article)

    assert passed is True
    assert article.status == ArticleStatus.SCORED
    assert article.curiosity_score == 9
    assert article.hidden_mechanism_score == 8.5


async def test_low_score_is_rejected(settings, article):
    llm = FakeLLMProvider(
        generate_responses=[
            json.dumps(
                {
                    "curiosity_score": 2,
                    "hidden_mechanism_score": 1,
                    "reason": "celebrity gossip",
                }
            )
        ]
    )
    service = CuriosityService(llm, settings)

    passed = await service.score_and_gate(article)

    assert passed is False
    assert article.status == ArticleStatus.REJECTED
    assert article.rejection_reason == "celebrity gossip"


async def test_mixed_score_below_one_threshold_rejected(settings, article):
    # High curiosity but low mechanism -> must fail (both thresholds required).
    llm = FakeLLMProvider(
        generate_responses=[
            json.dumps({"curiosity_score": 9, "hidden_mechanism_score": 3})
        ]
    )
    service = CuriosityService(llm, settings)
    assert await service.score_and_gate(article) is False
    assert article.status == ArticleStatus.REJECTED


async def test_malformed_response_defaults_to_rejected(settings, article):
    llm = FakeLLMProvider(generate_responses=["not json at all"])
    service = CuriosityService(llm, settings)
    assert await service.score_and_gate(article) is False
    assert article.status == ArticleStatus.REJECTED


async def test_scores_are_clamped(settings, article):
    llm = FakeLLMProvider(
        generate_responses=[
            json.dumps({"curiosity_score": 99, "hidden_mechanism_score": -4})
        ]
    )
    service = CuriosityService(llm, settings)
    score = await service.score_article(article)
    assert score.curiosity_score == 10
    assert score.hidden_mechanism_score == 0
