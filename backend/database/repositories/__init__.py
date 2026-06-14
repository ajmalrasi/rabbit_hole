"""Repository implementations encapsulating all database queries."""
from database.repositories.article_repo import ArticleRepository
from database.repositories.rabbit_hole_repo import RabbitHoleRepository

__all__ = ["ArticleRepository", "RabbitHoleRepository"]
