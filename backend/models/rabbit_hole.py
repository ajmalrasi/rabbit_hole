"""The generated "rabbit hole" - the core artefact of the application."""
from __future__ import annotations

from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from models.base import Base, TimestampMixin

_EMBEDDING_DIM = get_settings().embedding_dim


class RabbitHole(Base, TimestampMixin):
    """A curiosity-driven exploration of the hidden mechanism behind a topic."""

    __tablename__ = "rabbit_holes"
    __table_args__ = (
        Index("ix_rabbit_holes_category", "category"),
        Index("ix_rabbit_holes_in_feed", "in_feed"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=True, unique=True
    )

    # Structured rabbit hole content.
    title: Mapped[str] = mapped_column(String(512))
    observation: Mapped[str] = mapped_column(Text)
    question: Mapped[str] = mapped_column(Text)
    hidden_mechanism: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    interesting_fact: Mapped[str] = mapped_column(Text)
    why_it_matters: Mapped[str] = mapped_column(Text)
    follow_up_question: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(String(2048))

    # Scoring (carried over from the source article for ranking).
    curiosity_score: Mapped[float] = mapped_column(Float, default=0.0)
    hidden_mechanism_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Semantic embedding used for near-duplicate detection and search.
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(_EMBEDDING_DIM), nullable=True
    )

    # Feed membership.
    in_feed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    feed_rank: Mapped[Optional[int]] = mapped_column(nullable=True)

    article: Mapped[Optional["Article"]] = relationship(  # noqa: F821
        back_populates="rabbit_hole"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RabbitHole id={self.id} category={self.category!r} title={self.title!r}>"
