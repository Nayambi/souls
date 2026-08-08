"""
Camada de acesso a dados. Nenhuma lógica de negócio vive aqui — apenas
leitura/escrita. Cada função de escrita abre a sua própria transação
atómica (commit/rollback tudo-ou-nada), o que evita estados parciais
se o processo cair a meio de uma escrita.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from app.storage.db import get_session
from app.storage.models import Agent, Post, TopicSeen


# ---------------------------------------------------------------------------
# DTOs simples devolvidos pelo repositório (mantém a camada de storage
# desacoplada dos schemas Pydantic da API)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PostRecord:
    id: str
    created_at: datetime
    text: str
    rationale: str
    sources: list[str]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

async def create_agent(persona_name: str, persona_domain: str) -> str:
    """Cria um novo agente e devolve o seu id. Chamado uma única vez no /init."""
    async with get_session() as session:
        async with session.begin():
            agent = Agent(persona_name=persona_name, persona_domain=persona_domain)
            session.add(agent)
            await session.flush()
            agent_id = agent.id
        return agent_id


async def get_agent(agent_id: str) -> Agent | None:
    async with get_session() as session:
        result = await session.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Posts (feed público)
# ---------------------------------------------------------------------------

async def save_post(
    agent_id: str,
    text: str,
    rationale: str,
    sources: list[str],
    topic_key: str,
) -> PostRecord:
    """
    Persiste um novo post publicado. Escrita atómica única — o post só
    existe no feed depois do commit ter sucesso por completo.
    """
    async with get_session() as session:
        async with session.begin():
            post = Post(
                agent_id=agent_id,
                text=text,
                rationale=rationale,
                sources_json=json.dumps(sources, ensure_ascii=False),
                topic_key=topic_key,
            )
            session.add(post)
            await session.flush()
            record = PostRecord(
                id=post.id,
                created_at=post.created_at,
                text=post.text,
                rationale=post.rationale,
                sources=sources,
            )
        return record


async def get_feed(agent_id: str) -> list[PostRecord]:
    """Devolve todos os posts do agente, ordenados por created_at decrescente (mais recente primeiro)."""
    async with get_session() as session:
        result = await session.execute(
            select(Post).where(Post.agent_id == agent_id).order_by(Post.created_at.desc())
        )
        posts = result.scalars().all()
        return [
            PostRecord(
                id=p.id,
                created_at=p.created_at,
                text=p.text,
                rationale=p.rationale,
                sources=json.loads(p.sources_json),
            )
            for p in posts
        ]


# ---------------------------------------------------------------------------
# TopicSeen (memória interna / deduplicação)
# ---------------------------------------------------------------------------

async def record_topic_evaluation(
    agent_id: str,
    topic_key: str,
    title: str,
    source_url: str,
    decision: str,
    reasoning: str,
) -> None:
    """Regista todo tópico avaliado (publicado ou rejeitado) para memória futura."""
    async with get_session() as session:
        async with session.begin():
            session.add(
                TopicSeen(
                    agent_id=agent_id,
                    topic_key=topic_key,
                    title=title,
                    source_url=source_url,
                    decision=decision,
                    reasoning=reasoning,
                )
            )


async def get_recent_topic_keys(agent_id: str, limit: int = 100) -> set[str]:
    """
    Devolve o conjunto de topic_keys já avaliados recentemente (publicados
    ou rejeitados). Usado pelo editorial judgment para evitar reavaliar ou
    republicar o mesmo assunto.
    """
    async with get_session() as session:
        result = await session.execute(
            select(TopicSeen.topic_key)
            .where(TopicSeen.agent_id == agent_id)
            .order_by(TopicSeen.evaluated_at.desc())
            .limit(limit)
        )
        return set(result.scalars().all())


async def get_recent_published_summaries(agent_id: str, limit: int = 10) -> list[str]:
    """
    Devolve um pequeno resumo (título) dos últimos posts publicados, para
    dar contexto ao writer/editorial e evitar repetição de ângulo/conteúdo.
    """
    async with get_session() as session:
        result = await session.execute(
            select(TopicSeen.title)
            .where(TopicSeen.agent_id == agent_id, TopicSeen.decision == "publish")
            .order_by(TopicSeen.evaluated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
