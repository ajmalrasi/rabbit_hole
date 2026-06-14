"""Curiosity scoring service.

Scores each article on ``curiosity_score`` and ``hidden_mechanism_score`` using
the configured LLM, then gates low-quality articles out of the pipeline.
"""
from __future__ import annotations

import enum

from app.config import Settings
from app.logging_config import get_logger
from models.article import Article, ArticleStatus
from models.schemas import CuriosityScore
from prompts.curiosity import CURIOSITY_SYSTEM_PROMPT, build_curiosity_prompt
from services.json_utils import extract_json
from services.llm.base import LLMProvider

logger = get_logger(__name__)


class ScoreOutcome(str, enum.Enum):
    """Result of scoring + gating one article."""

    PASSED = "passed"
    REJECTED = "rejected"
    RETRY = "retry"  # transient LLM/network error — article stays NEW


class CuriosityService:
    def __init__(self, llm: LLMProvider, settings: Settings) -> None:
        self._llm = llm
        self._settings = settings

    async def score_article(self, article: Article) -> CuriosityScore:
        """Call the LLM to score one article. Raises on transient failure."""
        prompt = build_curiosity_prompt(
            title=article.title, summary=article.summary, source=article.source
        )
        raw = await self._llm.generate(
            prompt,
            system=CURIOSITY_SYSTEM_PROMPT,
            temperature=0.2,
            json_mode=True,
        )
        data = extract_json(raw)
        return CuriosityScore(
            curiosity_score=_clamp(data.get("curiosity_score", 0)),
            hidden_mechanism_score=_clamp(data.get("hidden_mechanism_score", 0)),
            reason=str(data.get("reason", ""))[:1000],
        )

    def passes_gate(self, score: CuriosityScore) -> bool:
        return (
            score.curiosity_score >= self._settings.min_curiosity_score
            and score.hidden_mechanism_score >= self._settings.min_hidden_mechanism_score
        )

    async def score_and_gate(self, article: Article) -> ScoreOutcome:
        """Score an article, persist results, and update its status.

        Transient LLM/network failures leave the article as NEW for a later retry.
        """
        try:
            score = await self.score_article(article)
        except Exception as exc:
            logger.warning(
                "Scoring deferred for article %s (will retry): %s", article.id, exc
            )
            return ScoreOutcome.RETRY

        article.curiosity_score = score.curiosity_score
        article.hidden_mechanism_score = score.hidden_mechanism_score

        if self.passes_gate(score):
            article.status = ArticleStatus.SCORED
            article.rejection_reason = None
            logger.info(
                "Article %s PASSED (curiosity=%.1f, mechanism=%.1f)",
                article.id,
                score.curiosity_score,
                score.hidden_mechanism_score,
            )
            return ScoreOutcome.PASSED

        article.status = ArticleStatus.REJECTED
        article.rejection_reason = score.reason or "below curiosity threshold"
        logger.info(
            "Article %s REJECTED (curiosity=%.1f, mechanism=%.1f)",
            article.id,
            score.curiosity_score,
            score.hidden_mechanism_score,
        )
        return ScoreOutcome.REJECTED


def _clamp(value: object, lo: float = 0.0, hi: float = 10.0) -> float:
    try:
        num = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    return max(lo, min(hi, num))
