"""APScheduler wiring for the background pipeline."""
from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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

    async def _run_daily_pipeline(self) -> None:
        """Once-daily: fetch RSS, score, generate rabbit holes, rebuild feed."""
        try:
            await self._pipeline.run(
                do_ingest=True,
                do_score=True,
                do_generate=True,
                drain=True,
            )
        except Exception:  # pragma: no cover - safety net for scheduled runs
            logger.exception("Scheduled daily pipeline run failed")

    def start(self) -> None:
        hour = self._settings.daily_pipeline_hour
        minute = self._settings.daily_pipeline_minute

        self._scheduler.add_job(
            self._run_daily_pipeline,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_pipeline",
            name="Daily ingest + score + generate + feed",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info(
            "Scheduler started: daily pipeline at %02d:%02d UTC",
            hour,
            minute,
        )

        if self._settings.run_on_startup:
            asyncio.create_task(self._delayed_initial_run())

    async def _delayed_initial_run(self) -> None:
        await asyncio.sleep(5)
        logger.info("Running initial pipeline pass on startup")
        await self._run_daily_pipeline()

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")
