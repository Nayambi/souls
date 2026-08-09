"""POST /api/agent/init — chamado exatamente uma vez pelo avaliador."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.schemas.api_models import InitRequest, InitResponse
from app.storage.repository import create_agent, set_next_cycle_at

router = APIRouter(prefix="/api/agent", tags=["agent"])

# Atraso antes do primeiro ciclo de um agente recém-criado. Mantido
# separado do intervalo entre ciclos (45min-3h, ver app/core/agent_cycle.py)
# porque o primeiro ciclo deve ser rápido — é o que dá o primeiro post
# do agente pouco depois do /init, sem esperar uma janela de horas.
FIRST_RUN_DELAY_SECONDS = int(
    os.environ.get("FIRST_RUN_DELAY_SECONDS", 30)
)


@router.post("/init", response_model=InitResponse)
async def init_agent(payload: InitRequest) -> InitResponse:
    agent_id = await create_agent(
        persona_name=payload.persona.name,
        persona_domain=payload.persona.domain,
    )

    # Agenda o primeiro ciclo diretamente na BD (next_cycle_at) — não há
    # aqui nenhum job a registar num scheduler externo. O poller interno
    # (app/scheduling/scheduler.py) e/ou uma chamada a POST
    # /api/agent/tick vão apanhar este agente assim que next_cycle_at
    # passar.
    first_run = datetime.now(timezone.utc) + timedelta(seconds=FIRST_RUN_DELAY_SECONDS)
    await set_next_cycle_at(agent_id, first_run)

    return InitResponse(agentId=agent_id)
