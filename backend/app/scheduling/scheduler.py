"""
Poller interno responsável por disparar os ciclos autónomos de publicação.

Desenho:
Em vez de um job do APScheduler por agente (um scheduler persistente,
com a sua própria BD, um trigger por agent_id), há agora UM único loop
assíncrono leve, correndo no mesmo event loop do servidor HTTP, que a
cada POLLER_INTERVAL_SECONDS pergunta à BD "que agentes estão devidos
agora?" (via claim_due_agent_ids, atómico) e corre o ciclo para cada um.

Isto simplifica bastante o modelo mental: não há jobstore persistido a
gerir, não há uma segunda BD SQLite (scheduler.db deixa de ser
necessária), e o intervalo real entre ciclos de um agente é decidido a
cada fim de ciclo (agent_cycle.run_publishing_cycle), não por um
trigger fixo — o que é o que permite ao intervalo ser 45min-3h
aleatório em vez de um valor fixo com jitter.

O mesmo efeito ("correr agora") também está disponível fora do loop
periódico via POST /api/agent/tick (app/api/routes_tick.py), que chama
run_due_cycles() diretamente — útil para testes/avaliação sem esperar
o intervalo real.
"""

from __future__ import annotations

import asyncio
import logging
import os

from app.core.agent_cycle import run_due_cycles

logger = logging.getLogger("scheduler")


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

# Cadência do loop interno — não é o intervalo entre posts de um agente
# (esse é 45min-3h, decidido em agent_cycle.py). É apenas de quanto em
# quanto tempo o poller verifica "há algum agente devido agora?". Um
# valor baixo (60s) mantém a latência entre "ficar devido" e "correr"
# pequena, sem custo relevante (a query é uma única UPDATE indexada).
POLLER_INTERVAL_SECONDS = int(
    os.environ.get("POLLER_INTERVAL_SECONDS", 60)
)

# Nº máximo de agentes reivindicados por tick (proteção contra um pico
# de agentes todos devidos ao mesmo tempo bloquear o poller demasiado
# tempo numa única iteração).
MAX_AGENTS_PER_TICK = int(
    os.environ.get("MAX_AGENTS_PER_TICK", 50)
)


# ---------------------------------------------------------------------------
# LOOP
# ---------------------------------------------------------------------------

_poller_task: asyncio.Task[None] | None = None
_stop_event: asyncio.Event | None = None


async def _poll_loop(stop_event: asyncio.Event) -> None:
    logger.info(
        "Poller interno arrancado | intervalo=%ds | max_por_tick=%d",
        POLLER_INTERVAL_SECONDS,
        MAX_AGENTS_PER_TICK,
    )

    while not stop_event.is_set():
        try:
            processed = await run_due_cycles(limit=MAX_AGENTS_PER_TICK)

            if processed:
                logger.info(
                    "Poller: %d ciclo(s) de publicação corridos.",
                    processed,
                )

        except Exception:
            # Um erro no tick não pode matar o loop — a próxima iteração
            # tenta de novo. Erros de um agente específico já são
            # apanhados dentro de run_publishing_cycle.
            logger.exception("Erro inesperado no poller interno.")

        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=POLLER_INTERVAL_SECONDS
            )
        except asyncio.TimeoutError:
            pass  # cadência normal — volta a correr o tick

    logger.info("Poller interno parado.")


# ---------------------------------------------------------------------------
# START / SHUTDOWN
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """
    Arranca o poller interno como uma asyncio.Task no event loop
    corrente. Tem de ser chamado a partir de dentro de um loop a correr
    (o lifespan do FastAPI, por exemplo) — não faz sentido standalone.
    """
    global _poller_task, _stop_event

    if _poller_task is not None and not _poller_task.done():
        logger.info("Poller já estava em execução.")
        return

    _stop_event = asyncio.Event()
    _poller_task = asyncio.create_task(_poll_loop(_stop_event))


async def shutdown_scheduler() -> None:
    """
    Sinaliza o loop para parar e espera que a iteração corrente termine
    antes de devolver — evita "Task was destroyed but it is pending"
    no shutdown do servidor.
    """
    global _poller_task, _stop_event

    if _stop_event is None or _poller_task is None:
        return

    logger.info("A encerrar poller interno...")

    _stop_event.set()

    try:
        await asyncio.wait_for(_poller_task, timeout=10)
    except asyncio.TimeoutError:
        logger.warning("Poller não parou a tempo, a cancelar à força.")
        _poller_task.cancel()

    _poller_task = None
    _stop_event = None
