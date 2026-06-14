"""FastAPI dependency providers (dependency injection wiring).

These functions assemble repositories and services from a request-scoped DB
session, keeping route handlers thin and testable.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from database.repositories.article_repo import ArticleRepository
from database.repositories.rabbit_hole_repo import RabbitHoleRepository
from database.session import get_db
from services.embedding_service import EmbeddingService
from services.feed_service import FeedService
from services.chat_service import ChatService
from services.llm.base import LLMProvider
from services.llm.factory import get_embedding_provider, get_chat_provider

SessionDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_article_repo(session: SessionDep) -> ArticleRepository:
    return ArticleRepository(session)


def get_rabbit_hole_repo(session: SessionDep) -> RabbitHoleRepository:
    return RabbitHoleRepository(session)


RabbitHoleRepoDep = Annotated[RabbitHoleRepository, Depends(get_rabbit_hole_repo)]
ArticleRepoDep = Annotated[ArticleRepository, Depends(get_article_repo)]


def get_feed_service(
    repo: RabbitHoleRepoDep, settings: SettingsDep
) -> FeedService:
    return FeedService(repo, settings)


def get_embedder() -> LLMProvider:
    return get_embedding_provider()


def get_embedding_service(
    repo: RabbitHoleRepoDep,
    settings: SettingsDep,
    embedder: Annotated[LLMProvider, Depends(get_embedder)],
) -> EmbeddingService:
    return EmbeddingService(embedder, repo, settings)


FeedServiceDep = Annotated[FeedService, Depends(get_feed_service)]
EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]


def get_chat_service(settings: SettingsDep) -> ChatService:
    return ChatService(settings, get_chat_provider())


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
