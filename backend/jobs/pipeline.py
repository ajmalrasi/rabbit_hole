"""End-to-end content pipeline.

Stages:
    1. Ingest articles from RSS feeds.
    2. Score new articles for curiosity / hidden mechanism, gating low quality.
    3. Generate rabbit holes for the articles that pass, with embedding-based
       near-duplicate rejection.
    4. Rebuild the daily feed.

The pipeline wires up repositories and services from a single DB session, so it
can be invoked from the scheduler, on startup, or from an admin endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings, get_settings
from app.logging_config import get_logger
from database.repositories.article_repo import ArticleRepository
from database.repositories.rabbit_hole_repo import RabbitHoleRepository
from database.session import session_scope
from models.article import ArticleStatus
from services.curiosity_service import CuriosityService
from services.embedding_service import EmbeddingService
from services.feed_service import FeedService
from services.llm.factory import get_embedding_provider, get_llm_provider
from services.rabbit_hole_service import RabbitHoleService
from services.rss_service import make_rss_service

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    ingested: int = 0
    scored: int = 0
    passed: int = 0
    rejected: int = 0
    generated: int = 0
    duplicates: int = 0
    failed: int = 0
    feed_size: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return self.__dict__


class ContentPipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = get_llm_provider()
        self._embedder = get_embedding_provider()

    async def ingest(self) -> int:
        with session_scope() as session:
            rss = make_rss_service(ArticleRepository(session))
            return await rss.ingest()

    async def score_pending(self, result: PipelineResult, *, drain: bool = False) -> None:
        """Score NEW articles. When ``drain`` is True, repeat until none remain."""
        batch = self._settings.max_articles_per_run
        while True:
            with session_scope() as session:
                repo = ArticleRepository(session)
                service = CuriosityService(self._llm, self._settings)
                articles = repo.list_by_status(ArticleStatus.NEW, limit=batch)
                if not articles:
                    break
                logger.info("Scoring %d new articles", len(articles))
                for article in articles:
                    passed = await service.score_and_gate(article)
                    result.scored += 1
                    result.passed += int(passed)
                    result.rejected += int(not passed)
                    session.commit()
            if not drain or len(articles) < batch:
                break

    async def generate_pending(self, result: PipelineResult, *, drain: bool = False) -> None:
        """Generate rabbit holes for SCORED articles. When ``drain`` is True, loop."""
        batch = self._settings.max_articles_per_run
        while True:
            with session_scope() as session:
                article_repo = ArticleRepository(session)
                rh_repo = RabbitHoleRepository(session)
                embedding_service = EmbeddingService(
                    self._embedder, rh_repo, self._settings
                )
                generator = RabbitHoleService(
                    self._llm, embedding_service, rh_repo, self._settings
                )
                articles = article_repo.list_by_status(
                    ArticleStatus.SCORED, limit=batch
                )
                if not articles:
                    break
                logger.info(
                    "Generating rabbit holes for %d scored articles", len(articles)
                )
                for article in articles:
                    rabbit_hole = await generator.generate_for_article(article)
                    if rabbit_hole is not None:
                        result.generated += 1
                    elif article.status == ArticleStatus.DUPLICATE:
                        result.duplicates += 1
                    else:
                        result.failed += 1
                    session.commit()
            if not drain or len(articles) < batch:
                break

    def rebuild_feed(self, result: PipelineResult) -> None:
        with session_scope() as session:
            feed_service = FeedService(RabbitHoleRepository(session), self._settings)
            result.feed_size = feed_service.generate_daily_feed()

    async def run(
        self,
        *,
        do_ingest: bool = True,
        do_score: bool = True,
        do_generate: bool = True,
        drain: bool | None = None,
    ) -> PipelineResult:
        """Run the full pipeline and return a summary of what happened.

        Each stage is independently toggleable:
        - ``do_ingest``   – fetch RSS feeds and store raw articles
        - ``do_score``    – curiosity-score NEW articles
        - ``do_generate`` – generate rabbit holes for SCORED articles
        - ``drain``       – loop score/generate until queues empty (default: config)
        """
        if drain is None:
            drain = self._settings.pipeline_drain_on_process

        result = PipelineResult()
        logger.info("=== Pipeline run started (drain=%s) ===", drain)

        if do_ingest:
            try:
                result.ingested = await self.ingest()
            except Exception as exc:
                logger.exception("Ingestion stage failed")
                result.errors.append(f"ingest: {exc}")

        if do_score:
            try:
                await self.score_pending(result, drain=drain)
            except Exception as exc:
                logger.exception("Scoring stage failed")
                result.errors.append(f"score: {exc}")

        if do_generate:
            try:
                await self.generate_pending(result, drain=drain)
            except Exception as exc:
                logger.exception("Generation stage failed")
                result.errors.append(f"generate: {exc}")

        try:
            self.rebuild_feed(result)
        except Exception as exc:
            logger.exception("Feed stage failed")
            result.errors.append(f"feed: {exc}")

        logger.info("=== Pipeline run finished: %s ===", result.as_dict())
        return result
