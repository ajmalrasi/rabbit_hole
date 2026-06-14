"""``GET /categories`` - available categories with counts."""
from __future__ import annotations

from fastapi import APIRouter

from api.deps import RabbitHoleRepoDep
from models.schemas import CategoriesResponse, CategoryCount

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=CategoriesResponse)
def get_categories(repo: RabbitHoleRepoDep) -> CategoriesResponse:
    counts = repo.category_counts()
    return CategoriesResponse(
        categories=[CategoryCount(category=c, count=n) for c, n in counts]
    )
