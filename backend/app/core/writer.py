"""
Gera o texto final do post, grounded estritamente no conteúdo já
recolhido pelo discovery (nunca deixa o modelo "completar de memória"
uma fonte que não leu). Produz também o rationale estruturado exigido
pela API (why selected, why relevant now, sources).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.core.discovery import TopicCandidate
from app.core.editorial import EditorialDecision
from app.core.llm_client import GeminiFatalError, GeminiRateLimitError, call_claude_text
from app.core.persona import Persona
from app.storage.repository import PostRecord


logger = logging.getLogger("writer")


# ---------------------------------------------------------------------------
# LIMITES LOCAIS
# ---------------------------------------------------------------------------

# Nº máximo de escritas de post concorrentes. Mesmo racional do
# _editorial_semaphore em editorial.py: protege o TPM caso o pipeline
# aprove vários candidatos no mesmo ciclo e os escreva com
# asyncio.gather em vez de sequencialmente.
_MAX_CONCURRENT_WRITES = 3
_writer_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_WRITES)

# Faixa de tamanho pedida ao modelo no prompt (400-800 caracteres).
# Não é reforçada à força (truncar destruiria o post), só logada como
# aviso quando o modelo foge do intervalo — sinal de possível prompt
# drift a acompanhar.
_MIN_EXPECTED_CHARS = 400
_MAX_EXPECTED_CHARS = 800


WRITER_SYSTEM_TEMPLATE = """{persona_block}

Vais agora escrever um post curto (estilo post de rede social profissional,
tipo thread inicial no X/LinkedIn) sobre o tópico fornecido. Regras:
- Usa APENAS a informação fornecida no resumo/contexto abaixo. Não inventes
  factos, números ou citações que não estão presentes na fonte.
- Mantém o teu tom e as tuas posições editoriais definidas acima.
- Entre 400 e 800 caracteres. Sem hashtags em excesso, sem emojis.
- Termina com uma opinião ou ângulo claro teu, não apenas um resumo neutro.
- Não repitas o ângulo, a estrutura de abertura, nem o conteúdo dos teus
  posts recentes listados abaixo — o objetivo é cada post trazer algo
  novo, mesmo quando o tema geral se sobrepõe.
- Não menciones as alternativas rejeitadas no texto do post; usa-as apenas
  para calibrar internamente o ângulo (por que este tópico, e não outro).
- Não menciones que és uma IA."""

WRITER_USER_TEMPLATE = """Tópico aprovado para publicação:
Título: {title}
Resumo/contexto (única fonte de factos permitida): {summary}
Fonte: {source_name} ({url})

Por que foi selecionado (usa isto para calibrar o ângulo do post):
{editorial_reasoning}

TEUS POSTS RECENTES (texto completo — não repitas ângulo, exemplos ou
conteúdo já usado aqui):
{recent_posts_block}

ALTERNATIVAS AVALIADAS E NÃO ESCOLHIDAS NESTE CICLO (contexto interno,
não mencionar no post):
{alternatives_block}

Escreve o post agora."""


@dataclass(frozen=True, slots=True)
class WrittenPost:
    text: str
    rationale: str
    sources: list[str]


def _build_rationale(candidate: TopicCandidate, decision: EditorialDecision) -> str:
    """
    Monta o rationale público a partir da decisão editorial já validada —
    não faz uma nova chamada ao modelo, reaproveita a justificação
    estruturada do EditorialDecision para garantir consistência entre
    o que foi "pensado" e o que é exposto na API.
    """
    return (
        f"Selecionado porque {decision.reasoning} "
        f"Relevante agora: {decision.relevance_now} "
        f"Pontuação de relevância atribuída: {decision.relevance_score}/10."
    )


def _format_recent_posts(recent_posts: list[PostRecord]) -> str:
    """
    Formata os posts recentes (texto completo, não só título) para o
    prompt do writer. Sem isto o writer só via títulos resumidos (via
    o editorial judgment), o que não chega para evitar repetir uma
    frase de abertura ou um exemplo já usado.
    """
    if not recent_posts:
        return "(ainda não há posts publicados)"

    blocks = []
    for post in recent_posts:
        blocks.append(f"---\n{post.text}")

    return "\n".join(blocks)


async def write_post(
    persona: Persona,
    candidate: TopicCandidate,
    decision: EditorialDecision,
    recent_posts: list[PostRecord] | None = None,
    alternatives_note: str = "(nenhuma alternativa foi avaliada e rejeitada neste ciclo)",
) -> WrittenPost:
    logger.info(
        "A escrever post para o tópico aprovado: %s",
        candidate.title,
    )

    system_prompt = WRITER_SYSTEM_TEMPLATE.format(persona_block=persona.system_prompt_block())
    user_prompt = WRITER_USER_TEMPLATE.format(
        title=candidate.title,
        summary=candidate.summary or "(sem resumo disponível, baseia-te apenas no título)",
        source_name=candidate.source_name,
        url=candidate.url,
        editorial_reasoning=decision.reasoning,
        recent_posts_block=_format_recent_posts(recent_posts or []),
        alternatives_block=alternatives_note,
    )

    try:
        text = await call_claude_text(system_prompt=system_prompt, user_prompt=user_prompt)

    except GeminiRateLimitError:
        logger.exception(
            "Quota do Gemini esgotada de forma persistente ao escrever post | tópico=%s",
            candidate.title,
        )
        raise

    except GeminiFatalError:
        logger.exception(
            "Erro fatal do Gemini ao escrever post | tópico=%s",
            candidate.title,
        )
        raise

    if not text.strip():
        raise RuntimeError(
            f"Gemini devolveu um post vazio para o tópico '{candidate.title}'."
        )

    if not (_MIN_EXPECTED_CHARS <= len(text) <= _MAX_EXPECTED_CHARS):
        logger.warning(
            "Post fora da faixa de tamanho esperada (%d-%d) | tópico=%s | tamanho=%d",
            _MIN_EXPECTED_CHARS,
            _MAX_EXPECTED_CHARS,
            candidate.title,
            len(text),
        )

    logger.info(
        "Post gerado com sucesso | tópico=%s | tamanho=%d",
        candidate.title,
        len(text),
    )

    return WrittenPost(
        text=text,
        rationale=_build_rationale(candidate, decision),
        sources=[candidate.url],
    )


async def write_post_bounded(
    persona: Persona,
    candidate: TopicCandidate,
    decision: EditorialDecision,
    recent_posts: list[PostRecord] | None = None,
    alternatives_note: str = "(nenhuma alternativa foi avaliada e rejeitada neste ciclo)",
) -> WrittenPost:
    """
    Wrapper com concorrência limitada.

    Usa esta função (em vez de write_post diretamente) sempre que
    escreveres vários posts aprovados em paralelo, ex.:

        posts = await asyncio.gather(*[
            write_post_bounded(persona, c, d)
            for c, d in approved_candidates
        ])

    O semáforo garante no máximo _MAX_CONCURRENT_WRITES chamadas
    ao Gemini em voo ao mesmo tempo, independentemente de quantos
    posts tenham sido aprovados no mesmo ciclo.
    """

    async with _writer_semaphore:
        return await write_post(
            persona,
            candidate,
            decision,
            recent_posts=recent_posts,
            alternatives_note=alternatives_note,
        )