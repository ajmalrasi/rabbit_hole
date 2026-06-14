"""FastAPI application entry point.

Wires together configuration, logging, database initialisation, the background
scheduler, and the HTTP routers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.routes import admin, categories, feed, rabbit_hole, search
from app import __version__
from app.config import get_settings
from app.logging_config import configure_logging, get_logger
from database.init_db import init_db
from database.session import engine
from jobs.scheduler import PipelineScheduler
from models.schemas import HealthResponse
from services.llm.factory import close_providers

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: init DB, start scheduler, clean up."""
    logger.info("Starting %s v%s (env=%s)", settings.app_name, __version__, settings.app_env)
    init_db()

    scheduler = PipelineScheduler(settings)
    scheduler.start()
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        logger.info("Shutting down")
        scheduler.shutdown()
        await close_providers()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="Discover the hidden mechanisms behind ordinary things.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(feed.router)
    app.include_router(rabbit_hole.router)
    app.include_router(categories.router)
    app.include_router(search.router)
    app.include_router(admin.router)

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        db_status = "ok"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:  # pragma: no cover - depends on live DB
            db_status = f"error: {exc}"
        return HealthResponse(
            status="ok",
            app=settings.app_name,
            version=__version__,
            llm_provider=settings.llm_provider,
            embedding_provider=settings.embedding_provider,
            database=db_status,
        )

    @app.get("/", tags=["system"])
    def root() -> dict:
        return {
            "app": settings.app_name,
            "version": __version__,
            "tagline": "What invisible system is causing this?",
            "docs": "/docs",
        }

    return app


app = create_app()
