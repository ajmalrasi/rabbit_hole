"""RSS ingestion service.

Fetches the configured feeds, parses entries, and stores new raw articles in
Postgres (skipping anything already ingested by GUID).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import mktime
from typing import Optional

import feedparser
import httpx

from app.logging_config import get_logger
from database.repositories.article_repo import ArticleRepository
from models.article import Article
from services.feeds import FEED_SOURCES, FeedSource

logger = get_logger(__name__)

# A descriptive UA avoids 403s from sources like Reddit.
_USER_AGENT = (
    "RabbitHoleBot/1.0 (+https://github.com/rabbit-hole; curiosity aggregator)"
)


class RSSService:
    """Fetches and persists articles from RSS/Atom feeds."""

    def __init__(
        self,
        article_repo: ArticleRepository,
        timeout: float = 30.0,
        sources: Optional[list[FeedSource]] = None,
    ) -> None:
        self._repo = article_repo
        self._timeout = timeout
        self._sources = sources or FEED_SOURCES

    async def _fetch_raw(self, client: httpx.AsyncClient, source: FeedSource) -> str:
        resp = await client.get(source.url)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_published(entry) -> Optional[datetime]:
        for key in ("published_parsed", "updated_parsed"):
            value = entry.get(key)
            if value:
                try:
                    return datetime.fromtimestamp(mktime(value), tz=timezone.utc)
                except (OverflowError, ValueError):
                    continue
        return None

    def _entry_to_article(self, source: FeedSource, entry) -> Optional[Article]:
        link = entry.get("link") or entry.get("id")
        title = (entry.get("title") or "").strip()
        if not link or not title:
            return None

        guid = entry.get("id") or link
        summary = entry.get("summary") or entry.get("description") or ""

        return Article(
            guid=guid[:1024],
            source=source.name,
            title=title[:1024],
            url=link[:2048],
            summary=summary,
            author=(entry.get("author") or None),
            published_at=self._parse_published(entry),
        )

    async def _fetch_source(
        self, client: httpx.AsyncClient, source: FeedSource
    ) -> list[Article]:
        try:
            raw = await self._fetch_raw(client, source)
        except Exception as exc:  # network errors, non-200, etc.
            logger.warning("Failed to fetch %s: %s", source.name, exc)
            return []

        parsed = feedparser.parse(raw)
        articles: list[Article] = []
        for entry in parsed.entries:
            article = self._entry_to_article(source, entry)
            if article is not None:
                articles.append(article)
        logger.info("Fetched %d entries from %s", len(articles), source.name)
        return articles

    async def fetch_all(self) -> list[Article]:
        """Fetch every configured source concurrently and return parsed articles."""
        headers = {"User-Agent": _USER_AGENT, "Accept": "application/rss+xml, */*"}
        async with httpx.AsyncClient(
            timeout=self._timeout, headers=headers, follow_redirects=True
        ) as client:
            results = await asyncio.gather(
                *(self._fetch_source(client, s) for s in self._sources)
            )
        return [article for batch in results for article in batch]

    async def ingest(self) -> int:
        """Fetch all feeds and persist new articles. Returns the count inserted."""
        articles = await self.fetch_all()

        # Deduplicate within this batch by GUID before hitting the DB.
        seen: set[str] = set()
        unique: list[Article] = []
        for article in articles:
            if article.guid in seen:
                continue
            seen.add(article.guid)
            unique.append(article)

        inserted = self._repo.bulk_insert_new(unique)
        self._repo.commit()
        logger.info(
            "Ingestion complete: %d fetched, %d new stored", len(unique), len(inserted)
        )
        return len(inserted)
