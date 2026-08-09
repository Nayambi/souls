"""Schemas Pydantic para request/response da API pública."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PersonaInit(BaseModel):
    name: str = Field(default="", max_length=120)
    domain: str = Field(default="", max_length=200)


class InitRequest(BaseModel):
    persona: PersonaInit


class InitResponse(BaseModel):
    agentId: str


class PostOut(BaseModel):
    id: str
    createdAt: datetime
    text: str
    rationale: str
    sources: list[str]

PostOutput = PostOut

class FeedResponse(BaseModel):
    posts: list[PostOut]


class TickResponse(BaseModel):
    processed: int
