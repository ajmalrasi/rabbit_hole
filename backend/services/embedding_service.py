"""Embedding generation and near-duplicate detection."""
from __future__ import annotations

from app.config import Settings
from app.logging_config import get_logger
from database.repositories.rabbit_hole_repo import RabbitHoleRepository
from models.schemas import RabbitHoleContent
from services.llm.base import LLMProvider

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(
        self,
        embedder: LLMProvider,
        rabbit_hole_repo: RabbitHoleRepository,
        settings: Settings,
    ) -> None:
        self._embedder = embedder
        self._repo = rabbit_hole_repo
        self._settings = settings

    @staticmethod
    def build_embedding_text(content: RabbitHoleContent) -> str:
        """Concatenate the most semantically meaningful fields for embedding."""
        return "\n".join(
            [
                content.title,
                content.observation,
                content.question,
                content.hidden_mechanism,
                content.explanation,
            ]
        ).strip()

    async def embed_text(self, text: str) -> list[float]:
        vector = await self._embedder.embed(text)
        expected = self._settings.embedding_dim
        if len(vector) != expected:
            logger.warning(
                "Embedding dimension mismatch: got %d, expected %d. "
                "Check EMBEDDING_DIM against your model.",
                len(vector),
                expected,
            )
        return vector

    def is_duplicate(self, embedding: list[float]) -> bool:
        """True if an existing rabbit hole is within the dedup distance threshold."""
        nearest = self._repo.nearest_distance(embedding)
        if nearest is None:
            return False
        is_dup = nearest < self._settings.dedup_distance_threshold
        if is_dup:
            logger.info(
                "Near-duplicate detected (distance=%.4f < threshold=%.4f)",
                nearest,
                self._settings.dedup_distance_threshold,
            )
        return is_dup
