"""GET /api/agent/feed — único endpoint consultado repetidamente pelo avaliador."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.api_models import FeedResponse, PostOut
from app.storage.repository import get_agent, get_feed

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/feed", response_model=FeedResponse)
async def read_feed(agentId: str = Query(...)) -> FeedResponse:
    agent = await get_agent(agentId)
    if agent is None:
        raise HTTPException(status_code=404, detail="agentId não encontrado")

    records = await get_feed(agentId)  # já vem ordenado created_at desc no repositório
    posts = [
        PostOut(
            id=r.id,
            createdAt=r.created_at,
            text=r.text,
            rationale=r.rationale,
            sources=r.sources,
        )
        for r in records
    ]
    return FeedResponse(posts=posts)
