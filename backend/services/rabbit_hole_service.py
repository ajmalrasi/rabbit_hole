"""Rabbit hole generation service.

Transforms a scored article into a structured rabbit hole, generates its
embedding, rejects near-duplicates, and persists the result.
"""
from __future__ import annotations

from typing import Optional

from app.config import Settings
from app.logging_config import get_logger
from database.repositories.rabbit_hole_repo import RabbitHoleRepository
from models.article import Article, ArticleStatus
from models.rabbit_hole import RabbitHole
from models.schemas import RabbitHoleContent
from prompts.rabbit_hole import (
    CATEGORIES,
    RABBIT_HOLE_SYSTEM_PROMPT,
    build_rabbit_hole_prompt,
)
from services.embedding_service import EmbeddingService
from services.json_utils import extract_json
from services.llm.base import LLMProvider

logger = get_logger(__name__)

_REQUIRED_FIELDS = (
    "title",
    "observation",
    "question",
    "hidden_mechanism",
    "explanation",
    "interesting_fact",
    "why_it_matters",
    "follow_up_question",
    "category",
)


class RabbitHoleService:
    def __init__(
        self,
        llm: LLMProvider,
        embedding_service: EmbeddingService,
        rabbit_hole_repo: RabbitHoleRepository,
        settings: Settings,
    ) -> None:
        self._llm = llm
        self._embeddings = embedding_service
        self._repo = rabbit_hole_repo
        self._settings = settings

    async def _generate_content(self, article: Article) -> RabbitHoleContent:
        prompt = build_rabbit_hole_prompt(
            title=article.title,
            summary=article.summary,
            source_url=article.url,
            allowed_categories=CATEGORIES,
        )
        raw = await self._llm.generate(
            prompt,
            system=RABBIT_HOLE_SYSTEM_PROMPT,
            temperature=0.7,
            json_mode=True,
        )
        data = extract_json(raw)

        missing = [f for f in _REQUIRED_FIELDS if not str(data.get(f, "")).strip()]
        if missing:
            raise ValueError(f"Generated rabbit hole missing fields: {missing}")

        data["source_url"] = article.url
        data["category"] = _normalise_category(data.get("category", "other"))
        return RabbitHoleContent(**{k: str(data[k]) for k in RabbitHoleContent.model_fields})

    async def generate_for_article(self, article: Article) -> Optional[RabbitHole]:
        """Full generation flow for a single scored article.

        Returns the created RabbitHole, or None if it was rejected as a duplicate
        or generation failed.
        """
        try:
            content = await self._generate_content(article)
        except Exception as exc:
            logger.warning("Generation failed for article %s: %s", article.id, exc)
            article.status = ArticleStatus.FAILED
            return None

        # Embed and dedup.
        embed_text = self._embeddings.build_embedding_text(content)
        try:
            embedding = await self._embeddings.embed_text(embed_text)
        except Exception as exc:
            logger.warning("Embedding failed for article %s: %s", article.id, exc)
            article.status = ArticleStatus.FAILED
            return None

        if self._embeddings.is_duplicate(embedding):
            article.status = ArticleStatus.DUPLICATE
            article.rejection_reason = "near-duplicate of existing rabbit hole"
            return None

        rabbit_hole = RabbitHole(
            article_id=article.id,
            title=content.title[:512],
            observation=content.observation,
            question=content.question,
            hidden_mechanism=content.hidden_mechanism,
            explanation=content.explanation,
            interesting_fact=content.interesting_fact,
            why_it_matters=content.why_it_matters,
            follow_up_question=content.follow_up_question,
            category=content.category,
            source_url=content.source_url[:2048],
            curiosity_score=article.curiosity_score or 0.0,
            hidden_mechanism_score=article.hidden_mechanism_score or 0.0,
            embedding=embedding,
        )
        self._repo.add(rabbit_hole)
        article.status = ArticleStatus.GENERATED
        logger.info(
            "Generated rabbit hole '%s' [%s] from article %s",
            rabbit_hole.title,
            rabbit_hole.category,
            article.id,
        )
        return rabbit_hole


def _normalise_category(value: str) -> str:
    candidate = (value or "").strip().lower()
    if candidate in CATEGORIES:
        return candidate
    # Map a few common synonyms onto the canonical vocabulary.
    synonyms = {
        "tech": "engineering",
        "technology": "engineering",
        "science": "physics",
        "space": "physics",
        "astronomy": "physics",
        "nature": "biology",
        "ecology": "biology",
        "sport": "sports science",
        "sports": "sports science",
        "finance": "economics",
        "construction": "architecture",
        "transport": "transportation",
        "geology": "earth science",
    }
    return synonyms.get(candidate, "other")
