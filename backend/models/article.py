"""Raw article ingested from an RSS feed."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Index, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin


class ArticleStatus(str, enum.Enum):
    """Lifecycle of an ingested article as it moves through the pipeline."""

    NEW = "new"               # freshly ingested, not yet scored
    SCORED = "scored"         # curiosity scoring complete
    REJECTED = "rejected"     # failed the curiosity / mechanism gate
    GENERATED = "generated"   # a rabbit hole was produced
    DUPLICATE = "duplicate"   # rabbit hole was a near-duplicate, discarded
    FAILED = "failed"         # an unrecoverable error occurred


class Article(Base, TimestampMixin):
    """A raw article collected from one of the configured feeds."""

    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_status", "status"),
        Index("ix_articles_source", "source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Stable de-duplication key for the *source* article (usually the URL).
    guid: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(1024))
    url: Mapped[str] = mapped_column(String(2048))
    summary: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    status: Mapped[ArticleStatus] = mapped_column(
        SAEnum(ArticleStatus, name="article_status"),
        default=ArticleStatus.NEW,
    )

    # Curiosity scoring results (populated by the scoring service).
    curiosity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hidden_mechanism_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    rabbit_hole: Mapped[Optional["RabbitHole"]] = relationship(  # noqa: F821
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Article id={self.id} source={self.source!r} status={self.status}>"
