"""
Camada de memória semântica via Breeth. Complementa o storage.repository
(que faz dedup exato por topic_key) com busca por significado — permite
ao editorial perceber tópicos *parecidos*, não só idênticos.
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("memory")

BREETH_BASE_URL = os.environ.get("BREETH_BASE_URL", "https://api.thebreeth.com/v1")
BREETH_API_KEY = os.environ.get("BREETH_API_KEY")


async def _post(path: str, payload: dict) -> dict | None:
    if not BREETH_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BREETH_BASE_URL}{path}",
                headers={
                    "Authorization": f"Bearer {BREETH_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError:
        # memória é um complemento, não pode derrubar o ciclo de publicação
        logger.exception("Breeth indisponível — a seguir sem contexto semântico")
        return None


async def search_similar_context(persona, candidates: list) -> list[str]:
    titles = ", ".join(c.title for c in candidates[:5])
    result = await _post("/search", {
        "query": f"posts já publicados sobre: {titles}",
        "limit": 5,
    })
    if not result:
        return []
    return [ep.get("narrative", "") for ep in result.get("results", [])]


async def record_publication(agent_id: str, topic_title: str, rationale: str, sources: list[str]) -> None:
    await _post("/episodes", {
        "messages": [
            {"role": "user", "content": f"[{agent_id}] Tópico selecionado: {topic_title}"},
            {"role": "assistant", "content": f"{rationale} Fontes: {', '.join(sources)}"},
        ]
    })