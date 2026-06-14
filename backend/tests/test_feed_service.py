"""Tests for daily feed generation and ranking."""
from __future__ import annotations

from models.rabbit_hole import RabbitHole
from services.feed_service import FeedService
from tests.conftest import FakeRabbitHoleRepo


def _rh(title: str, category: str, cs: float, hm: float) -> RabbitHole:
    return RabbitHole(
        title=title,
        observation="o",
        question="q",
        hidden_mechanism="h",
        explanation="e",
        interesting_fact="f",
        why_it_matters="w",
        follow_up_question="fu",
        category=category,
        source_url="https://example.com",
        curiosity_score=cs,
        hidden_mechanism_score=hm,
    )


def test_feed_selects_top_n_and_ranks(settings):
    repo = FakeRabbitHoleRepo()
    repo.items = [
        _rh("low", "physics", 1, 1),
        _rh("high", "engineering", 9, 9),
        _rh("mid", "biology", 5, 5),
        _rh("top", "physics", 10, 9),
    ]
    service = FeedService(repo, settings)

    size = service.generate_daily_feed()

    assert size == settings.daily_feed_size == 3
    feed = repo.list_feed(limit=10)
    titles = [rh.title for rh in feed]
    assert titles[0] == "top"
    assert "low" not in titles  # lowest scored dropped
    assert all(rh.feed_rank is not None for rh in feed)


def test_discouraged_content_excluded(settings):
    repo = FakeRabbitHoleRepo()
    repo.items = [
        _rh("Celebrity gossip roundup", "other", 10, 10),
        _rh("Bridge thermal expansion", "engineering", 7, 7),
    ]
    service = FeedService(repo, settings)

    service.generate_daily_feed()
    feed_titles = [rh.title for rh in repo.list_feed(limit=10)]

    assert "Celebrity gossip roundup" not in feed_titles
    assert "Bridge thermal expansion" in feed_titles


def test_priority_category_boost(settings):
    repo = FakeRabbitHoleRepo()
    # Equal base scores; priority category should rank above non-priority.
    repo.items = [
        _rh("generic", "other", 6, 6),
        _rh("priority", "physics", 6, 6),
    ]
    service = FeedService(repo, settings)
    service.generate_daily_feed()

    feed = repo.list_feed(limit=10)
    assert feed[0].title == "priority"
