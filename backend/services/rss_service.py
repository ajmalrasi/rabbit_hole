"""RSS ingestion service.

Fetches the configured feeds, parses entries, and stores new raw articles in
Postgres (skipping anything already ingested by GUID).

Feed content is cached on disk so repeated pipeline runs do not re-download
unchanged XML.  HTTP 304 conditional requests (ETag / If-Modified-Since) are
used whenever the upstream supports them.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import mktime
from typing import Optional

import feedparser
import httpx

from app.config import get_settings
from app.logging_config import get_logger
from database.repositories.article_repo import ArticleRepository
from models.article import Article
from services.feeds import FEED_SOURCES, FeedSource
from services.rss_cache import FeedCache

logger = get_logger(__name__)

_USER_AGENT = (
    "RabbitHoleBot/1.0 (+https://github.com/rabbit-hole; curiosity aggregator)"
)


class RSSService:
    """Fetches and persists articles from RSS/Atom feeds.

    Pass ``cache`` to enable disk caching (recommended for production). When the
    cache is fresh (age < TTL) the network is not touched at all for that feed.
    """

    def __init__(
        self,
        article_repo: ArticleRepository,
        timeout: float = 30.0,
        sources: Optional[list[FeedSource]] = None,
        cache: Optional[FeedCache] = None,
    ) -> None:
        self._repo = article_repo
        self._timeout = timeout
        self._sources = sources or FEED_SOURCES
        self._cache = cache

    # ------------------------------------------------------------------ #
    # Fetching                                                             #
    # ------------------------------------------------------------------ #

    async def _fetch_raw(
        self, client: httpx.AsyncClient, source: FeedSource
    ) -> str:
        """Fetch one feed, using the disk cache when possible.

        Strategy:
        1. Cache fresh?  → return cached XML, no network call.
        2. Cache stale but exists? → send conditional GET (ETag/Last-Modified).
           - 304 Not Modified → refresh timestamp, return cached XML.
           - 200 → save new content, return it.
        3. No cache → plain GET, save result.
        4. On any network failure → fall back to stale cache if available.
        """
        if self._cache:
            if self._cache.is_fresh(source.name):
                cached = self._cache.get_cached(source.name)
                if cached:
                    logger.debug("RSS cache HIT (fresh): %s", source.name)
                    return cached

            # Stale or missing — try a conditional GET.
            extra_headers = self._cache.get_conditional_headers(source.name)
        else:
            extra_headers = {}

        try:
            resp = await client.get(source.url, headers=extra_headers)

            if resp.status_code == 304 and self._cache:
                self._cache.mark_unchanged(source.name)
                cached = self._cache.get_cached(source.name)
                logger.info("RSS 304 (unchanged): %s", source.name)
                return cached or ""

            resp.raise_for_status()
            content = resp.text

            if self._cache:
                self._cache.save(
                    source.name,
                    content,
                    etag=resp.headers.get("ETag", ""),
                    last_modified=resp.headers.get("Last-Modified", ""),
                )
            return content

        except Exception as exc:
            if self._cache:
                stale = self._cache.get_cached(source.name)
                if stale:
                    logger.warning(
                        "Fetch failed for %s (%s) — using stale cache", source.name, exc
                    )
                    return stale
            raise

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
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", source.name, exc)
            return []

        if not raw:
            return []

        parsed = feedparser.parse(raw)
        articles: list[Article] = []
        for entry in parsed.entries:
            article = self._entry_to_article(source, entry)
            if article is not None:
                articles.append(article)
        logger.info("Parsed %d entries from %s", len(articles), source.name)
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

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    async def ingest(self) -> int:
        """Fetch all feeds and persist new articles. Returns the count inserted."""
        articles = await self.fetch_all()

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


def make_rss_service(article_repo: ArticleRepository) -> RSSService:
    """Build an RSSService wired to the configured disk cache."""
    settings = get_settings()
    cache: Optional[FeedCache] = None
    if settings.rss_cache_dir:
        cache = FeedCache(
            cache_dir=settings.rss_cache_dir,
            ttl_minutes=settings.rss_cache_ttl_minutes,
        )
    return RSSService(article_repo=article_repo, cache=cache)
