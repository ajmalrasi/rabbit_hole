"""Follow-up Q&A about a rabbit hole using ChatGPT (or fallback LLM)."""
from __future__ import annotations

from app.config import Settings
from app.logging_config import get_logger
from models.rabbit_hole import RabbitHole
from services.llm.base import LLMProvider
from services.llm.factory import get_chat_provider

logger = get_logger(__name__)

CHAT_SYSTEM_PROMPT = """You are a curious science educator helping someone explore \
a "Rabbit Hole" — an article about the hidden mechanisms behind everyday things.

Use the article context below to answer the user's question. Be clear, insightful, \
and conversational. If the question goes beyond the article, you may use general \
knowledge but say when you're extrapolating. Keep answers focused (2–4 short \
paragraphs max)."""


def _build_context(rh: RabbitHole) -> str:
    return f"""TITLE: {rh.title}
CATEGORY: {rh.category}
OBSERVATION: {rh.observation}
QUESTION: {rh.question}
HIDDEN MECHANISM: {rh.hidden_mechanism}
EXPLANATION: {rh.explanation}
INTERESTING FACT: {rh.interesting_fact}
WHY IT MATTERS: {rh.why_it_matters}
FOLLOW-UP QUESTION: {rh.follow_up_question}
SOURCE: {rh.source_url or "(none)"}"""


class ChatService:
    def __init__(self, settings: Settings, llm: LLMProvider | None = None) -> None:
        self._settings = settings
        self._llm = llm

    async def ask(self, rabbit_hole: RabbitHole, question: str) -> tuple[str, str]:
        """Return ``(answer, provider_name)``."""
        llm = self._llm or get_chat_provider()
        prompt = (
            f"{_build_context(rabbit_hole)}\n\n"
            f"USER QUESTION: {question.strip()}\n\n"
            "Answer the user's question:"
        )
        answer = await llm.generate(
            prompt,
            system=CHAT_SYSTEM_PROMPT,
            temperature=0.6,
        )
        logger.info(
            "Answered follow-up for rabbit hole %s via %s",
            rabbit_hole.id,
            llm.name,
        )
        return answer.strip(), llm.name
