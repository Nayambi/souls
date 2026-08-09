"""Contrato da API pública exigido pelo avaliador: /init e /feed."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_init_returns_agent_id(client: AsyncClient) -> None:
    response = await client.post(
        "/api/agent/init",
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert "agentId" in body
    assert isinstance(body["agentId"], str)
    assert body["agentId"]


@pytest.mark.asyncio
async def test_feed_empty_after_init(client: AsyncClient) -> None:
    init_response = await client.post(
        "/api/agent/init",
        json={"persona": {"name": "Ada", "domain": "AI Security"}},
    )
    agent_id = init_response.json()["agentId"]

    feed_response = await client.get(
        "/api/agent/feed",
        params={"agentId": agent_id},
    )

    assert feed_response.status_code == 200
    assert feed_response.json() == {"posts": []}


@pytest.mark.asyncio
async def test_feed_unknown_agent_returns_404(client: AsyncClient) -> None:
    response = await client.get(
        "/api/agent/feed",
        params={"agentId": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_feed_requires_agent_id(client: AsyncClient) -> None:
    response = await client.get("/api/agent/feed")

    assert response.status_code == 422
