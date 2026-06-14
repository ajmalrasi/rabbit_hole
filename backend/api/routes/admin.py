"""Admin / operational endpoints for manually driving the pipeline.

Split pipeline control:
  POST /admin/pipeline/run        – full run (ingest + score + generate + feed)
  POST /admin/pipeline/fetch      – RSS fetch + cache only, no LLM
  POST /admin/pipeline/process    – score + generate from DB, no network fetch
  POST /admin/feed/rebuild        – rebuild feed ranking from existing rabbit holes
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from api.deps import ArticleRepoDep, FeedServiceDep, RabbitHoleRepoDep, SettingsDep
from app import __version__
from app.logging_config import get_logger
from jobs.pipeline import ContentPipeline
from models.article import ArticleStatus
from models.schemas import (
    AdminStatusResponse,
    ArticleStatusCounts,
    PipelineCounters,
    PipelineRunState,
)
from services.pipeline_state import pipeline_state

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status", response_model=AdminStatusResponse)
def admin_status(
    article_repo: ArticleRepoDep,
    rabbit_hole_repo: RabbitHoleRepoDep,
    feed_service: FeedServiceDep,
    settings: SettingsDep,
) -> AdminStatusResponse:
    """Aggregate snapshot of content state + live pipeline progress."""
    counts = ArticleStatusCounts(
        new=article_repo.count_by_status(ArticleStatus.NEW),
        scored=article_repo.count_by_status(ArticleStatus.SCORED),
        rejected=article_repo.count_by_status(ArticleStatus.REJECTED),
        generated=article_repo.count_by_status(ArticleStatus.GENERATED),
        duplicate=article_repo.count_by_status(ArticleStatus.DUPLICATE),
        failed=article_repo.count_by_status(ArticleStatus.FAILED),
    )
    snap = pipeline_state.snapshot()
    pipeline = PipelineRunState(
        running=snap["running"],
        stage=snap["stage"],
        stage_total=snap["stage_total"],
        stage_processed=snap["stage_processed"],
        stage_elapsed_seconds=snap["stage_elapsed_seconds"],
        stage_eta_seconds=snap["stage_eta_seconds"],
        started_at=snap["started_at"],
        finished_at=snap["finished_at"],
        run_elapsed_seconds=snap["run_elapsed_seconds"],
        drain=snap["drain"],
        counters=PipelineCounters(**snap["counters"]),
        errors=snap["errors"],
    )
    return AdminStatusResponse(
        app=settings.app_name,
        version=__version__,
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
        database="ok",
        daily_feed_size=settings.daily_feed_size,
        total_rabbit_holes=rabbit_hole_repo.count(),
        feed_count=len(feed_service.get_feed(limit=settings.daily_feed_size)),
        articles=counts,
        pipeline=pipeline,
    )


def _already_running() -> dict:
    return {"status": "already_running", "stage": pipeline_state.snapshot()["stage"]}


@router.post("/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks, ingest: bool = True, drain: bool = False
) -> dict:
    """Full pipeline (ingest + score + generate + feed rebuild) in the background."""
    if pipeline_state.snapshot()["running"]:
        return _already_running()

    async def _run() -> None:
        await ContentPipeline().run(do_ingest=ingest, drain=drain)

    background_tasks.add_task(_run)
    return {
        "status": "scheduled",
        "stages": {"ingest": ingest, "score": True, "generate": True},
        "drain": drain,
    }


@router.post("/pipeline/fetch")
async def fetch_feeds(background_tasks: BackgroundTasks) -> dict:
    """Fetch RSS feeds and update the disk cache only. No LLM calls."""
    if pipeline_state.snapshot()["running"]:
        return _already_running()

    async def _run() -> None:
        await ContentPipeline().run(do_ingest=True, do_score=False, do_generate=False)

    background_tasks.add_task(_run)
    return {"status": "scheduled", "stages": {"ingest": True, "score": False, "generate": False}}


@router.post("/pipeline/process")
async def process_articles(background_tasks: BackgroundTasks, drain: bool = True) -> dict:
    """Score and generate from articles already in DB until the queue is empty."""
    if pipeline_state.snapshot()["running"]:
        return _already_running()

    async def _run() -> None:
        await ContentPipeline().run(
            do_ingest=False, do_score=True, do_generate=True, drain=drain
        )

    background_tasks.add_task(_run)
    return {
        "status": "scheduled",
        "stages": {"ingest": False, "score": True, "generate": True},
        "drain": drain,
    }


@router.post("/feed/rebuild")
def rebuild_feed(feed_service: FeedServiceDep) -> dict:
    """Synchronously rebuild the daily feed ranking from existing rabbit holes."""
    size = feed_service.generate_daily_feed()
    return {"status": "ok", "feed_size": size}
