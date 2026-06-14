"""Daily feed generation and read APIs.

Builds the curated daily feed by ranking rabbit holes with a score that blends
LLM quality signals with a boost for the priority categories the product cares
about.
"""
from __future__ import annotations

from app.config import Settings
from app.logging_config import get_logger
from database.repositories.rabbit_hole_repo import RabbitHoleRepository
from models.rabbit_hole import RabbitHole

logger = get_logger(__name__)

# Engineering-heavy topics we want to surface first in the daily feed.
ENGINEERING_CATEGORIES: frozenset[str] = frozenset(
    {
        "engineering",
        "infrastructure",
        "manufacturing",
        "architecture",
        "transportation",
    }
)

# Ranking boost per category. Higher = more likely to appear in the feed.
PRIORITY_CATEGORIES: dict[str, float] = {
    "engineering": 3.0,
    "infrastructure": 2.5,
    "manufacturing": 2.5,
    "architecture": 2.0,
    "transportation": 2.0,
    "physics": 1.5,
    "chemistry": 1.0,
    "geography": 1.0,
    "agriculture": 1.0,
    "sports science": 1.0,
    "economics": 1.0,
    "earth science": 0.5,
    "biology": 0.0,
    "other": 0.0,
}

# Minimum engineering-related slots when building a full daily feed.
MIN_ENGINEERING_FEED_ITEMS = 15

# Categories we actively avoid surfacing in the feed.
DISCOURAGED_KEYWORDS = (
    "celebrity",
    "politics",
    "gossip",
    "ai hype",
)


class FeedService:
    def __init__(
        self, rabbit_hole_repo: RabbitHoleRepository, settings: Settings
    ) -> None:
        self._repo = rabbit_hole_repo
        self._settings = settings

    def _rank_score(self, rh: RabbitHole) -> float:
        base = (rh.curiosity_score or 0.0) + (rh.hidden_mechanism_score or 0.0)
        boost = PRIORITY_CATEGORIES.get((rh.category or "").lower(), 0.0)
        penalty = 0.0
        haystack = f"{rh.title} {rh.category}".lower()
        if any(word in haystack for word in DISCOURAGED_KEYWORDS):
            penalty = 100.0  # effectively excludes it
        return base + boost - penalty

    def _select_feed_items(self, ranked: list[RabbitHole]) -> list[RabbitHole]:
        """Pick feed items, reserving slots for engineering-related topics."""
        feed_size = self._settings.daily_feed_size
        min_engineering = min(MIN_ENGINEERING_FEED_ITEMS, feed_size)

        engineering = [
            rh
            for rh in ranked
            if (rh.category or "").lower() in ENGINEERING_CATEGORIES
        ]

        selected: list[RabbitHole] = []
        seen: set[int] = set()

        def item_key(rh: RabbitHole) -> int:
            return rh.id if rh.id is not None else id(rh)

        for rh in engineering:
            if len(selected) >= min_engineering:
                break
            key = item_key(rh)
            if key in seen:
                continue
            seen.add(key)
            selected.append(rh)

        for rh in ranked:
            if len(selected) >= feed_size:
                break
            key = item_key(rh)
            if key in seen:
                continue
            seen.add(key)
            selected.append(rh)

        return selected

    def generate_daily_feed(self) -> int:
        """Recompute the daily feed. Returns the number of items selected."""
        candidates = self._repo.top_candidates(limit=200)
        ranked = sorted(candidates, key=self._rank_score, reverse=True)

        # Drop discouraged content entirely.
        ranked = [rh for rh in ranked if self._rank_score(rh) > -50]

        selected = self._select_feed_items(ranked)

        self._repo.clear_feed()
        for rank, rh in enumerate(selected, start=1):
            rh.in_feed = True
            rh.feed_rank = rank
        self._repo.commit()

        logger.info("Daily feed generated with %d rabbit holes", len(selected))
        return len(selected)

    def get_feed(
        self, limit: int = 20, offset: int = 0, category: str | None = None
    ) -> list[RabbitHole]:
        items = self._repo.list_feed(limit=limit, offset=offset, category=category)
        if items:
            return items
        # Cold start only on the first page when no feed has been built yet.
        if offset == 0 and self._repo.count_feed(category=category) == 0:
            return self._repo.top_candidates(limit=limit)
        return []

    def count_feed(self, category: str | None = None) -> int:
        total = self._repo.count_feed(category=category)
        if total > 0:
            return total
        return min(self._repo.count(), self._settings.daily_feed_size)
