"""POST /api/agent/init — chamado exatamente uma vez pelo avaliador."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.api_models import InitRequest, InitResponse
from app.scheduling.scheduler import schedule_agent_publishing
from app.storage.repository import create_agent

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/init", response_model=InitResponse)
async def init_agent(payload: InitRequest) -> InitResponse:
    agent_id = await create_agent(
        persona_name=payload.persona.name,
        persona_domain=payload.persona.domain,
    )

    # arranca a publicação autónoma para este agente — a partir daqui,
    # nenhuma outra chamada é necessária para que novos posts apareçam.
    schedule_agent_publishing(agent_id)

    return InitResponse(agentId=agent_id)
