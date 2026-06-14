"""``GET /rabbit-hole/{id}`` and follow-up Q&A."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.deps import ChatServiceDep, RabbitHoleRepoDep
from models.schemas import AskRequest, AskResponse, RabbitHoleOut

router = APIRouter(tags=["rabbit-hole"])


@router.get("/rabbit-hole/{rabbit_hole_id}", response_model=RabbitHoleOut)
def get_rabbit_hole(rabbit_hole_id: int, repo: RabbitHoleRepoDep) -> RabbitHoleOut:
    rabbit_hole = repo.get(rabbit_hole_id)
    if rabbit_hole is None:
        raise HTTPException(status_code=404, detail="Rabbit hole not found")
    return RabbitHoleOut.model_validate(rabbit_hole)


@router.post("/rabbit-hole/{rabbit_hole_id}/ask", response_model=AskResponse)
async def ask_about_rabbit_hole(
    rabbit_hole_id: int,
    body: AskRequest,
    repo: RabbitHoleRepoDep,
    chat_service: ChatServiceDep,
) -> AskResponse:
    """Ask a follow-up question about a rabbit hole (ChatGPT when configured)."""
    rabbit_hole = repo.get(rabbit_hole_id)
    if rabbit_hole is None:
        raise HTTPException(status_code=404, detail="Rabbit hole not found")
    try:
        answer, provider = await chat_service.ask(rabbit_hole, body.question)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not get an answer: {exc}",
        ) from exc
    return AskResponse(answer=answer, provider=provider)
