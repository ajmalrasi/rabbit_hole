"""Database initialisation: enable pgvector and create tables.

For a project of this scope ``create_all`` is sufficient and keeps deployment on
the Jetson simple. A migration tool (Alembic) can be layered on later without
changing the model definitions.
"""
from __future__ import annotations

from sqlalchemy import text

from app.logging_config import get_logger
from database.session import engine
from models.base import Base

# Import models so they register on the metadata before create_all runs.
import models  # noqa: F401

logger = get_logger(__name__)


def init_db() -> None:
    """Ensure the pgvector extension exists and all tables are created."""
    logger.info("Initialising database schema")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready")
