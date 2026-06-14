"""Repository for :class:`~models.rabbit_hole.RabbitHole`."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select

from database.repositories.base import BaseRepository
from models.rabbit_hole import RabbitHole


class RabbitHoleRepository(BaseRepository[RabbitHole]):
    model = RabbitHole

    # ----- listing / retrieval -----

    def list_feed(
        self, limit: int = 20, offset: int = 0, category: str | None = None
    ) -> list[RabbitHole]:
        stmt = self._feed_select(category)
        stmt = (
            stmt.order_by(RabbitHole.feed_rank.asc().nullslast(), RabbitHole.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())

    def count_feed(self, category: str | None = None) -> int:
        stmt = select(func.count()).select_from(RabbitHole).where(
            RabbitHole.in_feed.is_(True)
        )
        if category:
            stmt = stmt.where(func.lower(RabbitHole.category) == category.lower())
        return self.session.scalar(stmt) or 0

    def _feed_select(self, category: str | None = None):
        stmt = select(RabbitHole).where(RabbitHole.in_feed.is_(True))
        if category:
            stmt = stmt.where(func.lower(RabbitHole.category) == category.lower())
        return stmt

    def list_by_category(
        self, category: str, limit: int = 20, offset: int = 0
    ) -> list[RabbitHole]:
        stmt = (
            select(RabbitHole)
            .where(func.lower(RabbitHole.category) == category.lower())
            .order_by(RabbitHole.curiosity_score.desc(), RabbitHole.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())

    def category_counts(self) -> list[tuple[str, int]]:
        stmt = (
            select(RabbitHole.category, func.count())
            .group_by(RabbitHole.category)
            .order_by(func.count().desc())
        )
        return [(row[0], row[1]) for row in self.session.execute(stmt).all()]

    # ----- search -----

    def text_search(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> list[RabbitHole]:
        like = f"%{query}%"
        stmt = (
            select(RabbitHole)
            .where(
                or_(
                    RabbitHole.title.ilike(like),
                    RabbitHole.observation.ilike(like),
                    RabbitHole.question.ilike(like),
                    RabbitHole.hidden_mechanism.ilike(like),
                    RabbitHole.explanation.ilike(like),
                    RabbitHole.category.ilike(like),
                )
            )
            .order_by(RabbitHole.curiosity_score.desc(), RabbitHole.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())

    def semantic_search(
        self, embedding: list[float], limit: int = 20
    ) -> list[tuple[RabbitHole, float]]:
        """Return rabbit holes ordered by cosine distance to ``embedding``."""
        distance = RabbitHole.embedding.cosine_distance(embedding)
        stmt = (
            select(RabbitHole, distance.label("distance"))
            .where(RabbitHole.embedding.is_not(None))
            .order_by(distance.asc())
            .limit(limit)
        )
        return [(row[0], float(row[1])) for row in self.session.execute(stmt).all()]

    def nearest_distance(self, embedding: list[float]) -> Optional[float]:
        """Cosine distance to the single closest existing rabbit hole."""
        distance = RabbitHole.embedding.cosine_distance(embedding)
        stmt = (
            select(distance)
            .where(RabbitHole.embedding.is_not(None))
            .order_by(distance.asc())
            .limit(1)
        )
        result = self.session.scalar(stmt)
        return float(result) if result is not None else None

    # ----- feed management -----

    def clear_feed(self) -> None:
        for rh in self.session.scalars(
            select(RabbitHole).where(RabbitHole.in_feed.is_(True))
        ):
            rh.in_feed = False
            rh.feed_rank = None

    def top_candidates(self, limit: int = 100) -> list[RabbitHole]:
        """Highest-scoring rabbit holes, used to build the daily feed."""
        combined = RabbitHole.curiosity_score + RabbitHole.hidden_mechanism_score
        stmt = (
            select(RabbitHole)
            .order_by(combined.desc(), RabbitHole.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(RabbitHole)) or 0
