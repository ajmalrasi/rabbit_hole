"""``GET /search`` - keyword or semantic search over rabbit holes."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.deps import EmbeddingServiceDep, RabbitHoleRepoDep
from app.logging_config import get_logger
from models.schemas import SearchResponse, SearchResult

logger = get_logger(__name__)

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    repo: RabbitHoleRepoDep,
    embedding_service: EmbeddingServiceDep,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    semantic: bool = Query(
        True, description="Use vector similarity search (falls back to keyword)"
    ),
) -> SearchResponse:
    """Search rabbit holes by meaning (semantic) or keyword.

    Semantic search embeds the query and ranks by cosine similarity. If the
    embedding backend is unavailable, it transparently falls back to keyword
    search.
    """
    results: list[SearchResult] = []

    if semantic:
        try:
            embedding = await embedding_service.embed_text(q)
            hits = repo.semantic_search(embedding, limit=limit)
            results = [
                SearchResult(**_summary_fields(rh), distance=dist) for rh, dist in hits
            ]
        except Exception as exc:
            logger.warning("Semantic search failed, falling back to keyword: %s", exc)

    if not results:
        rows = repo.text_search(q, limit=limit)
        results = [SearchResult(**_summary_fields(rh)) for rh in rows]

    return SearchResponse(query=q, count=len(results), results=results)


def _summary_fields(rh) -> dict:
    return {
        "id": rh.id,
        "title": rh.title,
        "observation": rh.observation,
        "question": rh.question,
        "category": rh.category,
        "curiosity_score": rh.curiosity_score,
        "hidden_mechanism_score": rh.hidden_mechanism_score,
        "source_url": rh.source_url,
        "created_at": rh.created_at,
    }
