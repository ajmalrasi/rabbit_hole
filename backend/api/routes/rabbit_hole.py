"""``GET /rabbit-hole/{id}`` - fetch a single rabbit hole."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.deps import RabbitHoleRepoDep
from models.schemas import RabbitHoleOut

router = APIRouter(tags=["rabbit-hole"])


@router.get("/rabbit-hole/{rabbit_hole_id}", response_model=RabbitHoleOut)
def get_rabbit_hole(rabbit_hole_id: int, repo: RabbitHoleRepoDep) -> RabbitHoleOut:
    rabbit_hole = repo.get(rabbit_hole_id)
    if rabbit_hole is None:
        raise HTTPException(status_code=404, detail="Rabbit hole not found")
    return RabbitHoleOut.model_validate(rabbit_hole)
