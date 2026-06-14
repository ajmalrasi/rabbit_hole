"""Generic repository base class implementing common CRUD helpers."""
from __future__ import annotations

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Base repository wrapping a SQLAlchemy ``Session`` and a model type."""

    model: Type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, obj_id: int) -> Optional[ModelT]:
        return self.session.get(self.model, obj_id)

    def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        self.session.flush()
        return obj

    def list(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt).all())

    def delete(self, obj: ModelT) -> None:
        self.session.delete(obj)

    def commit(self) -> None:
        self.session.commit()
