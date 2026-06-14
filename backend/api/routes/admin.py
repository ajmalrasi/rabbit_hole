"""Admin / operational endpoints for manually driving the pipeline.

Split pipeline control:
  POST /admin/pipeline/run        – full run (ingest + score + generate + feed)
  POST /admin/pipeline/fetch      – RSS fetch + cache only, no LLM
  POST /admin/pipeline/process    – score + generate from DB, no network fetch
  POST /admin/feed/rebuild        – rebuild feed ranking from existing rabbit holes
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from api.deps import FeedServiceDep
from app.logging_config import get_logger
from jobs.pipeline import ContentPipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/pipeline/run")
async def run_pipeline(background_tasks: BackgroundTasks, ingest: bool = True) -> dict:
    """Full pipeline (ingest + score + generate + feed rebuild) in the background."""

    async def _run() -> None:
        await ContentPipeline().run(do_ingest=ingest)

    background_tasks.add_task(_run)
    return {"status": "scheduled", "stages": {"ingest": ingest, "score": True, "generate": True}}


@router.post("/pipeline/fetch")
async def fetch_feeds(background_tasks: BackgroundTasks) -> dict:
    """Fetch RSS feeds and update the disk cache only. No LLM calls."""

    async def _run() -> None:
        await ContentPipeline().run(do_ingest=True, do_score=False, do_generate=False)

    background_tasks.add_task(_run)
    return {"status": "scheduled", "stages": {"ingest": True, "score": False, "generate": False}}


@router.post("/pipeline/process")
async def process_articles(background_tasks: BackgroundTasks) -> dict:
    """Score and generate from articles already in DB. No network fetch."""

    async def _run() -> None:
        await ContentPipeline().run(do_ingest=False, do_score=True, do_generate=True)

    background_tasks.add_task(_run)
    return {"status": "scheduled", "stages": {"ingest": False, "score": True, "generate": True}}


@router.post("/feed/rebuild")
def rebuild_feed(feed_service: FeedServiceDep) -> dict:
    """Synchronously rebuild the daily feed ranking from existing rabbit holes."""
    size = feed_service.generate_daily_feed()
    return {"status": "ok", "feed_size": size}
