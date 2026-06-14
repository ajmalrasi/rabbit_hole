"""Repository for :class:`~models.article.Article`."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select

from database.repositories.base import BaseRepository
from models.article import Article, ArticleStatus


class ArticleRepository(BaseRepository[Article]):
    model = Article

    def get_by_guid(self, guid: str) -> Optional[Article]:
        stmt = select(Article).where(Article.guid == guid)
        return self.session.scalars(stmt).first()

    def exists_by_guid(self, guid: str) -> bool:
        stmt = select(func.count()).select_from(Article).where(Article.guid == guid)
        return (self.session.scalar(stmt) or 0) > 0

    def list_by_status(
        self, status: ArticleStatus, limit: int = 100
    ) -> list[Article]:
        stmt = (
            select(Article)
            .where(Article.status == status)
            .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def bulk_insert_new(self, articles: list[Article]) -> list[Article]:
        """Insert articles, skipping any whose GUID already exists."""
        inserted: list[Article] = []
        for article in articles:
            if self.exists_by_guid(article.guid):
                continue
            self.session.add(article)
            inserted.append(article)
        self.session.flush()
        return inserted

    def count_by_status(self, status: ArticleStatus) -> int:
        stmt = select(func.count()).select_from(Article).where(Article.status == status)
        return self.session.scalar(stmt) or 0
