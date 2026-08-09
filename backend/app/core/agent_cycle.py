
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
write() [com contexto de posts recentes + nota de alternativas rejeitadas]
    ↓
save_post()
    ↓
agendar o próximo ciclo (45min-3h a partir de agora)

Este módulo não depende directamente de FastAPI, e não depende do
scheduler (app/scheduling/scheduler.py importa DESTE módulo, nunca o
contrário — evita import circular).
"""

from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timedelta, timezone

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
    claim_due_agent_ids,
    get_agent,
    get_recent_published_posts,
    get_recent_published_summaries,
    get_recent_topic_keys,
    record_topic_evaluation,
    save_post,
    set_next_cycle_at,
)

from app.core.breeth import record_publication, search_similar_context

logger = logging.getLogger("agent_cycle")


MAX_CANDIDATES_TO_JUDGE = 8

# Nº de posts recentes (texto completo) mostrados ao writer como
# contexto, para não repetir ângulo/conteúdo já publicado.
MAX_RECENT_POSTS_FOR_WRITER = 5

# Janela de agendamento do próximo ciclo. Um intervalo fixo faria todos
# os agentes publicarem em cadência previsível; aleatorizar entre
# 45min e 3h é o que dá o comportamento "autónomo" pedido, sem nunca
# deixar um agente parado indefinidamente nem publicar demasiado
# depressa.
NEXT_CYCLE_MIN_MINUTES = int(os.environ.get("NEXT_CYCLE_MIN_MINUTES", 45))
NEXT_CYCLE_MAX_MINUTES = int(os.environ.get("NEXT_CYCLE_MAX_MINUTES", 180))


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
# AGENDAMENTO DO PRÓXIMO CICLO
# ---------------------------------------------------------------------------

def _pick_next_interval() -> timedelta:
    """Escolhe um intervalo aleatório dentro da janela 45min-3h."""
    minutes = random.uniform(NEXT_CYCLE_MIN_MINUTES, NEXT_CYCLE_MAX_MINUTES)
    return timedelta(minutes=minutes)


async def _schedule_next_cycle(agent_id: str) -> None:
    """
    Agenda o próximo ciclo deste agente a partir de agora. Chamado
    sempre no fim de run_publishing_cycle (sucesso OU falha) — ver
    comentário em run_publishing_cycle sobre porquê isto vive num
    finally.
    """
    next_run = datetime.now(timezone.utc) + _pick_next_interval()

    await set_next_cycle_at(agent_id, next_run)

    logger.info(
        "[%s] Próximo ciclo agendado para %s",
        agent_id,
        next_run.isoformat(),
    )


# ---------------------------------------------------------------------------
# NOTA DE ALTERNATIVAS REJEITADAS
# ---------------------------------------------------------------------------

def _build_alternatives_note(
    rejected: list[tuple[TopicCandidate, EditorialDecision]],
) -> str:
    """
    Constrói uma nota textual sobre os candidatos que foram avaliados
    neste mesmo ciclo mas NÃO escolhidos (rejeitados pelo editorial
    judgment, ou com score inferior ao vencedor). Passada ao writer
    como contexto adicional — não para os mencionar no post, mas para
    que o ângulo escolhido para o tópico vencedor seja implicitamente
    calibrado sabendo o que mais estava "na mesa" e porquê não foi
    esse o escolhido.

    Devolve uma string vazia com uma nota neutra quando não houve
    alternativas (só um candidato foi avaliado, ou nenhum foi
    rejeitado).
    """
    if not rejected:
        return "(nenhuma alternativa foi avaliada e rejeitada neste ciclo)"

    lines = []
    for candidate, decision in rejected:
        lines.append(
            f"- \"{candidate.title}\" (fonte: {candidate.source_name}) — "
            f"não escolhido: {decision.reasoning}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

async def run_publishing_cycle(agent_id: str) -> None:
    """
    Ponto de entrada utilizado pelo poller interno e por
    POST /api/agent/tick.

    Excepções são capturadas aqui para que um ciclo falhado não pare o
    poller nem impeça os restantes agentes devidos no mesmo tick de
    correrem.

    O reagendamento do próximo ciclo (_schedule_next_cycle) corre num
    finally: acontece sempre, quer o ciclo tenha tido sucesso, tenha
    sido abortado sem candidatos aprovados, ou tenha rebentado com uma
    excepção. Isto é o que garante que um agente nunca fica "preso" —
    sem isto, uma falha a meio deixaria next_cycle_at parado no
    marcador provisório de claim_due_agent_ids (30 min), e o agente
    seria reivindicado repetidamente em loop apertado até o próximo
    sucesso.
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

    finally:
        try:
            await _schedule_next_cycle(agent_id)
        except Exception:
            logger.exception(
                "[%s] ERRO AO AGENDAR O PRÓXIMO CICLO",
                agent_id,
            )

    logger.info(
        "=================================================="
    )


async def run_due_cycles(limit: int = 50) -> int:
    """
    Reivindica atomicamente os agentes devidos neste momento
    (claim_due_agent_ids) e corre o ciclo de publicação para cada um,
    sequencialmente. Chamado pelo poller interno a cada tick e por
    POST /api/agent/tick.

    Devolve o número de agentes processados neste tick.
    """
    now = datetime.now(timezone.utc)

    due_agent_ids = await claim_due_agent_ids(now=now, limit=limit)

    if not due_agent_ids:
        return 0

    logger.info(
        "Tick: %d agente(s) devido(s) | ids=%s",
        len(due_agent_ids),
        due_agent_ids,
    )

    for agent_id in due_agent_ids:
        await run_publishing_cycle(agent_id)

    return len(due_agent_ids)


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

    # Candidatos avaliados mas não escolhidos (rejeitados, ou aprovados
    # mas superados por um score melhor) — alimenta
    # _build_alternatives_note para dar contexto ao writer.
    rejected_evaluations: list[tuple[TopicCandidate, EditorialDecision]] = []

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

                rejected_evaluations.append((candidate, decision))
                continue

            if (
                best_decision is None
                or decision.relevance_score
                > best_decision.relevance_score
            ):
                # O anterior "melhor" (se existir) passa a alternativa
                # rejeitada — foi aprovado mas superado.
                if best_decision is not None and best_candidate is not None:
                    rejected_evaluations.append((best_candidate, best_decision))

                best_decision = decision
                best_candidate = candidate

                logger.info(
                    "[%s] Novo melhor candidato | %s | score=%s",
                    agent_id,
                    candidate.title,
                    decision.relevance_score,
                )
            else:
                rejected_evaluations.append((candidate, decision))

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

    recent_posts = await get_recent_published_posts(
        agent_id,
        limit=MAX_RECENT_POSTS_FOR_WRITER,
    )

    alternatives_note = _build_alternatives_note(rejected_evaluations)

    written = await write_post(
        persona,
        best_candidate,
        best_decision,
        recent_posts=recent_posts,
        alternatives_note=alternatives_note,
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
