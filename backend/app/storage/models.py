"""
SQLAlchemy ORM models (async).

Três tabelas:
- Agent: um registo por agente inicializado (persona + metadata)
- Post: o feed público, o que é devolvido em GET /api/agent/feed
- TopicSeen: memória interna do agente — todo tópico avaliado (publicado
  ou rejeitado), usado para deduplicação e para dar contexto ao editorial
  judgment sobre o que já foi coberto.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    persona_name: Mapped[str] = mapped_column(String(120), nullable=False)
    persona_domain: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Próximo instante em que o poller interno deve correr um ciclo de
    # publicação para este agente. NULL = ainda não agendado (nenhum ciclo
    # corre até algo definir este valor). Indexado porque é o campo usado
    # pelo claim atómico (WHERE next_cycle_at <= :now) a cada tick.
    next_cycle_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    posts: Mapped[list["Post"]] = relationship(back_populates="agent", cascade="all, delete-orphan")
    topics_seen: Mapped[list["TopicSeen"]] = relationship(back_populates="agent", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[str] = mapped_column(Text, nullable=False)  # lista JSON serializada
    topic_key: Mapped[str] = mapped_column(String(300), nullable=False)  # usado para dedup

    agent: Mapped["Agent"] = relationship(back_populates="posts")


class TopicSeen(Base):
    """
    Regista TODO tópico avaliado pelo editorial judgment, publicado ou não.
    Isto é o que permite ao agente evitar reavaliar/repetir o mesmo assunto
    em ciclos futuros, e dá transparência sobre o "raciocínio" ao longo do tempo.
    """

    __tablename__ = "topics_seen"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    topic_key: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)  # "publish" | "reject"
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    agent: Mapped["Agent"] = relationship(back_populates="topics_seen")
