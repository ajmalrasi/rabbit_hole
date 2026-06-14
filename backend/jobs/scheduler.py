"""APScheduler wiring for the background pipeline."""
from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import Settings, get_settings
from app.logging_config import get_logger
from jobs.pipeline import ContentPipeline

logger = get_logger(__name__)


class PipelineScheduler:
    """Owns the AsyncIOScheduler and registers the pipeline jobs."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._pipeline = ContentPipeline(self._settings)

    async def _run_pipeline(self) -> None:
        try:
            await self._pipeline.run(do_ingest=True)
        except Exception:  # pragma: no cover - safety net for scheduled runs
            logger.exception("Scheduled pipeline run failed")

    async def _run_feed_only(self) -> None:
        try:
            await asyncio.to_thread(self._rebuild_feed_sync)
        except Exception:  # pragma: no cover
            logger.exception("Scheduled feed rebuild failed")

    def _rebuild_feed_sync(self) -> None:
        from jobs.pipeline import PipelineResult

        self._pipeline.rebuild_feed(PipelineResult())

    def start(self) -> None:
        # Periodic full pipeline (ingest + score + generate + feed).
        self._scheduler.add_job(
            self._run_pipeline,
            trigger=IntervalTrigger(minutes=self._settings.ingest_interval_minutes),
            id="content_pipeline",
            name="Ingest + score + generate + feed",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        # Dedicated daily feed rebuild at a fixed hour.
        self._scheduler.add_job(
            self._run_feed_only,
            trigger=CronTrigger(hour=self._settings.daily_feed_hour, minute=0),
            id="daily_feed",
            name="Daily feed rebuild",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info(
            "Scheduler started: pipeline every %d min, daily feed at %02d:00 UTC",
            self._settings.ingest_interval_minutes,
            self._settings.daily_feed_hour,
        )

        if self._settings.run_on_startup:
            # Kick off an initial run shortly after boot without blocking startup.
            asyncio.create_task(self._delayed_initial_run())

    async def _delayed_initial_run(self) -> None:
        await asyncio.sleep(5)
        logger.info("Running initial pipeline pass on startup")
        await self._run_pipeline()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
