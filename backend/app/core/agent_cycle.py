
"""
Orquestra um ciclo completo de publicação:

discover()
    ↓
filtrar duplicados
    ↓
judge()
    ↓
escolher melhor candidato
    ↓
write()
    ↓
save_post()

Este módulo não depende directamente de FastAPI.
"""

from __future__ import annotations

import logging

from app.core.discovery import (
    TopicCandidate,
    discover_topics,
)
from app.core.editorial import (
    EditorialDecision,
    judge_topic,
)
from app.core.persona import (
    Persona,
    default_persona,
)
from app.core.writer import write_post

from app.storage.repository import (
    get_agent,
    get_recent_published_summaries,
    get_recent_topic_keys,
    record_topic_evaluation,
    save_post,
)

from app.core.breeth import record_publication, search_similar_context

logger = logging.getLogger("agent_cycle")


MAX_CANDIDATES_TO_JUDGE = 8


# ---------------------------------------------------------------------------
# PERSONA
# ---------------------------------------------------------------------------

async def _persona_for_agent(agent_id: str) -> Persona:
    """
    Reconstrói a persona a partir do agente guardado na BD.
    """

    logger.info(
        "[%s] A carregar persona...",
        agent_id,
    )

    from app.core.persona import persona_from_init_payload

    agent = await get_agent(agent_id)

    if agent is None:
        logger.warning(
            "[%s] Agente não encontrado. "
            "Será utilizada a persona default.",
            agent_id,
        )

        return default_persona()

    persona = persona_from_init_payload(
        agent.persona_name,
        agent.persona_domain,
    )

    logger.info(
        "[%s] Persona carregada | name=%s | domain=%s",
        agent_id,
        persona.name,
        persona.domain,
    )

    return persona


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

async def run_publishing_cycle(agent_id: str) -> None:
    """
    Ponto de entrada utilizado pelo APScheduler.

    Excepções são capturadas aqui para que um ciclo falhado
    não mate o scheduler.
    """

    logger.info(
        "=================================================="
    )

    logger.info(
        "[%s] INÍCIO DO CICLO DE PUBLICAÇÃO",
        agent_id,
    )

    try:
        await _run_cycle_unsafe(agent_id)

        logger.info(
            "[%s] CICLO TERMINADO",
            agent_id,
        )

    except Exception:
        logger.exception(
            "[%s] ERRO DURANTE O CICLO DE PUBLICAÇÃO",
            agent_id,
        )

    logger.info(
        "=================================================="
    )


# ---------------------------------------------------------------------------
# CICLO
# ---------------------------------------------------------------------------

async def _run_cycle_unsafe(agent_id: str) -> None:

    # ---------------------------------------------------------
    # 1. PERSONA
    # ---------------------------------------------------------

    persona = await _persona_for_agent(agent_id)

    # ---------------------------------------------------------
    # 2. DISCOVERY
    # ---------------------------------------------------------

    logger.info(
        "[%s] A iniciar descoberta de tópicos...",
        agent_id,
    )

    candidates = await discover_topics()

    logger.info(
        "[%s] Discovery terminou | candidatos=%d",
        agent_id,
        len(candidates),
    )

    if not candidates:
        logger.warning(
            "[%s] Nenhum tópico foi descoberto.",
            agent_id,
        )

        return

    for candidate in candidates[:10]:
        logger.info(
            "[%s] Candidato | %s | fonte=%s",
            agent_id,
            candidate.title,
            candidate.source_name,
        )

    # ---------------------------------------------------------
    # 3. MEMÓRIA / DEDUPLICAÇÃO
    # ---------------------------------------------------------

    logger.info(
        "[%s] A consultar tópicos já avaliados...",
        agent_id,
    )

    already_seen = await get_recent_topic_keys(agent_id)

    logger.info(
        "[%s] Tópicos já avaliados=%d",
        agent_id,
        len(already_seen),
    )

    fresh_candidates = [
        candidate
        for candidate in candidates
        if candidate.topic_key not in already_seen
    ]

    logger.info(
        "[%s] Candidatos novos=%d",
        agent_id,
        len(fresh_candidates),
    )

    if not fresh_candidates:
        logger.info(
            "[%s] Todos os candidatos já foram avaliados.",
            agent_id,
        )

        return

    # ---------------------------------------------------------
    # 4. POSTS RECENTES
    # ---------------------------------------------------------

    recent_titles = await get_recent_published_summaries(
        agent_id
    )

    logger.info(
        "[%s] Posts publicados anteriormente=%d",
        agent_id,
        len(recent_titles),
    )

    # ---------------------------------------------------------
    # 5. EDITORIAL JUDGMENT
    # ---------------------------------------------------------

    best_decision: EditorialDecision | None = None
    best_candidate: TopicCandidate | None = None

    candidates_to_judge = fresh_candidates[
        :MAX_CANDIDATES_TO_JUDGE
    ]

    logger.info(
        "[%s] A avaliar %d candidatos com o modelo...",
        agent_id,
        len(candidates_to_judge),
    )

    for index, candidate in enumerate(
        candidates_to_judge,
        start=1,
    ):

        logger.info(
            "[%s] Avaliação %d/%d | %s",
            agent_id,
            index,
            len(candidates_to_judge),
            candidate.title,
        )

        try:

            decision = await judge_topic(
                persona,
                candidate,
                recent_titles,
            )

            logger.info(
                "[%s] Resultado | decision=%s | score=%s | "
                "topic=%s",
                agent_id,
                decision.decision,
                decision.relevance_score,
                candidate.title,
            )

            await record_topic_evaluation(
                agent_id=agent_id,
                topic_key=candidate.topic_key,
                title=candidate.title,
                source_url=candidate.url,
                decision=decision.decision,
                reasoning=decision.reasoning,
            )

            if decision.decision != "publish":
                logger.info(
                    "[%s] Candidato rejeitado | %s",
                    agent_id,
                    candidate.title,
                )

                continue

            if (
                best_decision is None
                or decision.relevance_score
                > best_decision.relevance_score
            ):
                best_decision = decision
                best_candidate = candidate

                logger.info(
                    "[%s] Novo melhor candidato | %s | score=%s",
                    agent_id,
                    candidate.title,
                    decision.relevance_score,
                )

        except Exception:
            logger.exception(
                "[%s] Erro ao avaliar candidato: %s",
                agent_id,
                candidate.title,
            )

    # ---------------------------------------------------------
    # 6. NENHUM APROVADO
    # ---------------------------------------------------------

    if (
        best_decision is None
        or best_candidate is None
    ):

        logger.warning(
            "[%s] Nenhum candidato foi aprovado neste ciclo.",
            agent_id,
        )

        return

    logger.info(
        "[%s] Candidato seleccionado | %s",
        agent_id,
        best_candidate.title,
    )

    # ---------------------------------------------------------
    # 7. WRITER
    # ---------------------------------------------------------

    logger.info(
        "[%s] A gerar post...",
        agent_id,
    )

    written = await write_post(
        persona,
        best_candidate,
        best_decision,
    )

    logger.info(
        "[%s] Post gerado | caracteres=%d",
        agent_id,
        len(written.text),
    )

    # ---------------------------------------------------------
    # 8. PERSISTÊNCIA
    # ---------------------------------------------------------

    logger.info(
        "[%s] A guardar post na BD...",
        agent_id,
    )

    saved = await save_post(
        agent_id=agent_id,
        text=written.text,
        rationale=written.rationale,
        sources=written.sources,
        topic_key=best_candidate.topic_key,
    )

    logger.info(
        "[%s] POST GUARDADO COM SUCESSO | id=%s | "
        "topic=%s",
        agent_id,
        saved.id,
        best_candidate.title,
    )

