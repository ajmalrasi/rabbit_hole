"""Admin / operational endpoints for manually driving the pipeline."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from api.deps import FeedServiceDep
from app.logging_config import get_logger
from jobs.pipeline import ContentPipeline

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/pipeline/run")
async def run_pipeline(background_tasks: BackgroundTasks, ingest: bool = True) -> dict:
    """Trigger a full pipeline run in the background."""

    async def _run() -> None:
        pipeline = ContentPipeline()
        await pipeline.run(do_ingest=ingest)

    background_tasks.add_task(_run)
    return {"status": "scheduled", "ingest": ingest}


@router.post("/feed/rebuild")
def rebuild_feed(feed_service: FeedServiceDep) -> dict:
    """Synchronously rebuild the daily feed from existing rabbit holes."""
    size = feed_service.generate_daily_feed()
    return {"status": "ok", "feed_size": size}
