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

# Categories the product wants to surface, with a small ranking boost each.
PRIORITY_CATEGORIES: dict[str, float] = {
    "physics": 1.0,
    "engineering": 1.0,
    "biology": 1.0,
    "geography": 1.0,
    "infrastructure": 1.0,
    "architecture": 1.0,
    "transportation": 1.0,
    "agriculture": 1.0,
    "manufacturing": 1.0,
    "sports science": 1.0,
    "economics": 1.0,
}

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

    def generate_daily_feed(self) -> int:
        """Recompute the daily feed. Returns the number of items selected."""
        candidates = self._repo.top_candidates(limit=200)
        ranked = sorted(candidates, key=self._rank_score, reverse=True)

        # Drop discouraged content entirely.
        ranked = [rh for rh in ranked if self._rank_score(rh) > -50]

        selected = ranked[: self._settings.daily_feed_size]

        self._repo.clear_feed()
        for rank, rh in enumerate(selected, start=1):
            rh.in_feed = True
            rh.feed_rank = rank
        self._repo.commit()

        logger.info("Daily feed generated with %d rabbit holes", len(selected))
        return len(selected)

    def get_feed(self, limit: int = 20, offset: int = 0) -> list[RabbitHole]:
        items = self._repo.list_feed(limit=limit, offset=offset)
        if items:
            return items
        # Cold start: if no feed has been generated yet, fall back to top scored.
        return self._repo.top_candidates(limit=limit)
