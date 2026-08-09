"""Contrato do feed: ordenação, campos obrigatórios e serialização ISO 8601 UTC."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from app.schemas.api_models import FeedResponse, PostOut


def test_feed_response_empty_json() -> None:
    assert FeedResponse(posts=[]).model_dump() == {"posts": []}


def test_post_out_serializes_created_at_as_utc_iso() -> None:
    created = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    post = PostOut(
        id="550e8400-e29b-41d4-a716-446655440000",
        createdAt=created,
        text="Post de teste.",
        rationale="Rationale de teste com comprimento suficiente.",
        sources=["https://example.com/article"],
    )

    data = post.model_dump(mode="json")

    assert data["id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert data["createdAt"] == "2026-01-15T12:00:00Z"
    assert data["sources"] == ["https://example.com/article"]


@pytest.mark.asyncio
async def test_get_feed_orders_newest_first() -> None:
    from app.storage.db import init_db
    from app.storage.repository import create_agent, get_feed, save_post

    await init_db()

    agent_id = await create_agent("FeedTest", "AI Security")

    first = await save_post(
        agent_id=agent_id,
        text="Primeiro post.",
        rationale="Primeiro rationale publicado.",
        sources=["https://example.com/1"],
        topic_key="topic-1",
    )
    await asyncio.sleep(0.05)
    second = await save_post(
        agent_id=agent_id,
        text="Segundo post.",
        rationale="Segundo rationale publicado.",
        sources=["https://example.com/2"],
        topic_key="topic-2",
    )

    records = await get_feed(agent_id)

    assert len(records) == 2
    assert records[0].id == second.id
    assert records[1].id == first.id
    assert records[0].created_at >= records[1].created_at


@pytest.mark.asyncio
async def test_saved_posts_have_unique_ids() -> None:
    from app.storage.db import init_db
    from app.storage.repository import create_agent, save_post

    await init_db()

    agent_id = await create_agent("UniqueIds", "AI Security")

    first = await save_post(
        agent_id=agent_id,
        text="A",
        rationale="Rationale A.",
        sources=["https://example.com/a"],
        topic_key="a",
    )
    second = await save_post(
        agent_id=agent_id,
        text="B",
        rationale="Rationale B.",
        sources=["https://example.com/b"],
        topic_key="b",
    )

    assert first.id != second.id
