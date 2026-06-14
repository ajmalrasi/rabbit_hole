"""``GET /feed`` - the curated daily feed of rabbit holes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Query

from api.deps import FeedServiceDep
from models.schemas import FeedResponse, RabbitHoleSummary

router = APIRouter(tags=["feed"])


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    feed_service: FeedServiceDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> FeedResponse:
    """Return the top rabbit holes in the current daily feed."""
    items = feed_service.get_feed(limit=limit, offset=offset)
    return FeedResponse(
        count=len(items),
        generated_at=datetime.now(timezone.utc),
        items=[RabbitHoleSummary.model_validate(rh) for rh in items],
    )
