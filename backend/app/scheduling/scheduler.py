"""
Scheduler responsável pelos ciclos autónomos de publicação.

IMPORTANTE:
O APScheduler utiliza uma BD SQLite própria (scheduler.db).
A aplicação utiliza agent.db para os dados de negócio.

Isto evita que o SQLAlchemy síncrono usado pelo APScheduler
partilhe o mesmo ficheiro SQLite utilizado pelo SQLAlchemy async
da aplicação.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.agent_cycle import run_publishing_cycle


logger = logging.getLogger("scheduler")


# ---------------------------------------------------------------------------
# DIRECTÓRIO DE DADOS
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# JOBSTORE
# ---------------------------------------------------------------------------
#
# NÃO utilizar agent.db aqui.
#
# agent.db:
#   - agents
#   - posts
#   - topics_seen
#
# scheduler.db:
#   - tabelas internas do APScheduler
#
# ---------------------------------------------------------------------------

_SCHEDULER_DB = Path(
    os.environ.get("SCHEDULER_DB_PATH", _DATA_DIR / "scheduler.db")
)
_SCHEDULER_DB.parent.mkdir(parents=True, exist_ok=True)

_JOBSTORE_URL = f"sqlite:///{_SCHEDULER_DB}"


scheduler = AsyncIOScheduler(
    timezone="UTC",
    jobstores={
        "default": SQLAlchemyJobStore(
            url=_JOBSTORE_URL
        )
    },
    job_defaults={
        "misfire_grace_time": 60 * 30,
    },
)


# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

PUBLISH_INTERVAL_MINUTES = int(
    os.environ.get(
        "PUBLISH_INTERVAL_MINUTES",
        4 * 60,
    )
)

JITTER_SECONDS = int(
    os.environ.get(
        "PUBLISH_JITTER_SECONDS",
        45 * 60,
    )
)

FIRST_RUN_DELAY_SECONDS = int(
    os.environ.get(
        "FIRST_RUN_DELAY_SECONDS",
        30,
    )
)


# ---------------------------------------------------------------------------
# AGENDAMENTO
# ---------------------------------------------------------------------------

def schedule_agent_publishing(agent_id: str) -> None:
    """
    Agenda o ciclo autónomo de publicação para um agente.

    O primeiro ciclo ocorre após FIRST_RUN_DELAY_SECONDS.
    Os seguintes ocorrem de acordo com PUBLISH_INTERVAL_MINUTES.
    """

    if not agent_id:
        raise ValueError("agent_id não pode estar vazio.")

    first_run = (
        datetime.now(timezone.utc)
        + timedelta(seconds=FIRST_RUN_DELAY_SECONDS)
    )

    job_id = f"publish-{agent_id}"

    scheduler.add_job(
        run_publishing_cycle,
        trigger=IntervalTrigger(
            minutes=PUBLISH_INTERVAL_MINUTES,
            jitter=JITTER_SECONDS,
        ),
        args=[agent_id],
        id=job_id,
        next_run_time=first_run,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "Job de publicação agendado | agent_id=%s | "
        "primeiro ciclo=%s | intervalo=%d min",
        agent_id,
        first_run.isoformat(),
        PUBLISH_INTERVAL_MINUTES,
    )


# ---------------------------------------------------------------------------
# START / SHUTDOWN
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """
    Inicia o APScheduler e restaura jobs persistidos.
    """

    if scheduler.running:
        logger.info("Scheduler já estava em execução.")
        return

    scheduler.start()

    jobs = scheduler.get_jobs()

    logger.info(
        "Scheduler iniciado | jobs restaurados=%d | db=%s",
        len(jobs),
        _SCHEDULER_DB,
    )

    for job in jobs:
        logger.info(
            "Job restaurado | id=%s | próxima execução=%s",
            job.id,
            job.next_run_time,
        )


def shutdown_scheduler() -> None:
    """
    Encerra o scheduler.
    """

    if not scheduler.running:
        return

    logger.info("A encerrar scheduler...")

    scheduler.shutdown(wait=False)

    logger.info("Scheduler encerrado.")