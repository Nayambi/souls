"""
POST /api/agent/tick — dispara imediatamente run_due_cycles().

Não recebe agentId: corre para TODOS os agentes que estejam devidos
neste momento (mesma lógica que o poller interno usa periodicamente).
Existe para permitir forçar um ciclo (testes, avaliação, debugging)
sem esperar pelo intervalo real de 45min-3h nem pela cadência do
poller.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.agent_cycle import run_due_cycles
from app.schemas.api_models import TickResponse

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/tick", response_model=TickResponse)
async def tick() -> TickResponse:
    processed = await run_due_cycles()
    return TickResponse(processed=processed)
