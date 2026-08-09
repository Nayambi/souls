from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.discovery import TopicCandidate
from app.core.persona import Persona
from app.core.llm_client import call_claude_structured


logger = logging.getLogger("editorial")


# ---------------------------------------------------------------------------
# LIMITES LOCAIS
# ---------------------------------------------------------------------------

_MAX_CONCURRENT_JUDGEMENTS = 3
_editorial_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_JUDGEMENTS)

_MAX_RECENT_TITLES = 15


class EditorialDecision(BaseModel):
    decision: Literal["publish", "reject"]

    reasoning: str = Field(min_length=15)

    relevance_score: int = Field(
        ge=1,
        le=10,
    )

    matches_persona_interests: bool

    is_duplicate_or_stale: bool

    relevance_now: str = Field(min_length=1)

    manifesto_rule: str = Field(min_length=1)


EDITORIAL_SYSTEM_TEMPLATE = """
You are the editorial decision engine of an autonomous AI security
content creator.

PERSONA:
{persona_block}

EDITORIAL MANIFESTO (numbered, stable rules — you MUST cite exactly one
of these identifiers, e.g. "M2", in the manifesto_rule field of your
JSON response, followed by a short restatement of that rule in your own
words):
{manifesto_block}

Your task is to determine whether a discovered topic should become
a post for this persona.

IMPORTANT:
Do NOT be excessively restrictive.
Keep explanations concise, sharp and directly to the point.

A topic does not need to contain the exact words from the persona.
Evaluate the technical relationship between the topic and the persona.

Relevant areas include:

- AI security
- LLM security
- AI agents
- autonomous agents
- adversarial AI
- model attacks
- model vulnerabilities
- prompt injection
- jailbreaks
- red teaming
- AI safety
- AI incidents
- security testing of AI systems
- AI-related cyber attacks
- model supply chain
- vulnerabilities in AI products
- security research
- open-source AI security
- attacks performed by AI models
- AI models interacting with real systems
- security implications of new AI capabilities

A topic can be relevant even when the connection is indirect.

SCORING:

1-2: Clearly unrelated to the persona.
3-4: Weak relationship.
5-6: Reasonably relevant.
7-8: Clearly relevant.
9-10: Extremely relevant and highly important.

PUBLISH when:
- the topic has a reasonable technical connection to the persona;
- OR it describes a real AI/security incident;
- OR it describes a new security technique;
- OR it describes an attack, vulnerability, model behaviour,
  security research or AI capability with security implications.

REJECT only when:
- the topic is clearly unrelated;
- it is purely promotional;
- it is meaningless or extremely superficial;
- it is a duplicate of a recent post.

Return ONLY valid JSON strictly matching the requested schema.

manifesto_rule is REQUIRED and must never be an empty string.
"""


EDITORIAL_USER_TEMPLATE = """
Evaluate this candidate.

TITLE:
{title}

SUMMARY:
{summary}

SOURCE:
{source}

URL:
{url}

RECENT POSTS:
{recent_posts}

Remember:
The question is NOT: "Does this title exactly match the persona keywords?"
The question is: "Can this topic produce a technically valuable post for this AI security audience?"

Return ONLY JSON.
"""


def _clean_json_response(raw: str) -> str:
    """
    Remove markdown code fences e whitespace extra.
    """
    text = raw.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text


class _MalformedJsonError(Exception):
    """
    JSON inválido devolvido pelo modelo — falha de sintaxe do modelo.
    """


class _MissingManifestoRuleError(Exception):
    """
    Validation error específico para quando apenas manifesto_rule falta.
    """


def _is_missing_manifesto_rule_only(exc: ValidationError) -> bool:
    errors = exc.errors()
    if not errors:
        return False
    return all(error["loc"] == ("manifesto_rule",) for error in errors)


@retry(
    retry=retry_if_exception_type((_MalformedJsonError, _MissingManifestoRuleError)),
    wait=wait_fixed(1),
    stop=stop_after_attempt(2),
    reraise=True,
)
async def _call_and_parse(system_prompt: str, user_prompt: str, topic_title: str) -> EditorialDecision:
    # Aumentado max_tokens para 2048 e injetado o response_schema para Structured Outputs
    raw_response = await call_claude_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=2048,
        response_schema=EditorialDecision,
    )

    logger.info(
        "Resposta bruta do Gemini para '%s': %s",
        topic_title,
        raw_response,
    )

    try:
        cleaned = _clean_json_response(raw_response)
        logger.debug("JSON limpo: %s", cleaned)
        data = json.loads(cleaned)

    except Exception as exc:
        logger.warning(
            "JSON malformado devolvido pelo modelo | tópico=%s | resposta=%r",
            topic_title,
            raw_response,
        )
        raise _MalformedJsonError(str(exc)) from exc

    try:
        return EditorialDecision.model_validate(data)

    except ValidationError as exc:
        if _is_missing_manifesto_rule_only(exc):
            logger.warning(
                "manifesto_rule em falta/vazio na resposta do modelo | "
                "tópico=%s — a tentar novamente.",
                topic_title,
            )
            raise _MissingManifestoRuleError(str(exc)) from exc

        logger.exception(
            "ERRO DE VALIDAÇÃO EditorialDecision | tópico=%s | data=%r",
            topic_title,
            data,
        )
        raise


async def judge_topic(
    persona: Persona,
    candidate: TopicCandidate,
    recent_published_titles: list[str],
) -> EditorialDecision:

    logger.info(
        "A avaliar tópico editorialmente: %s",
        candidate.title,
    )

    persona_block = persona.system_prompt_block()

    manifesto_block = (
        "\n".join(
            f"M{index}: {stance}"
            for index, stance in enumerate(persona.editorial_stances, start=1)
        )
        if persona.editorial_stances
        else "(nenhuma posição editorial definida para esta persona)"
    )

    system_prompt = EDITORIAL_SYSTEM_TEMPLATE.format(
        persona_block=persona_block,
        manifesto_block=manifesto_block,
    )

    bounded_titles = recent_published_titles[-_MAX_RECENT_TITLES:]

    recent_posts = (
        "\n".join(
            f"- {title}"
            for title in bounded_titles
        )
        if bounded_titles
        else "(nenhum post publicado)"
    )

    user_prompt = EDITORIAL_USER_TEMPLATE.format(
        title=candidate.title,
        summary=candidate.summary or "(sem resumo)",
        source=candidate.source_name,
        url=candidate.url,
        recent_posts=recent_posts,
    )

    logger.debug(
        "Persona enviada ao modelo: %s",
        persona_block,
    )

    try:
        decision = await _call_and_parse(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            topic_title=candidate.title,
        )

    except _MalformedJsonError as exc:
        logger.exception(
            "ERRO AO FAZER PARSE DO JSON (após retry) | tópico=%s",
            candidate.title,
        )
        raise RuntimeError(
            "Gemini devolveu uma resposta que não é JSON válido."
        ) from exc

    except _MissingManifestoRuleError as exc:
        logger.exception(
            "Gemini não incluiu manifesto_rule mesmo após nova tentativa | "
            "tópico=%s",
            candidate.title,
        )
        raise RuntimeError(
            "Gemini não incluiu manifesto_rule na decisão editorial, "
            "mesmo após uma nova tentativa."
        ) from exc

    except ValidationError:
        logger.exception(
            "ERRO DE VALIDAÇÃO EditorialDecision | tópico=%s",
            candidate.title,
        )
        raise

    except Exception:
        logger.exception(
            "ERRO AO CHAMAR GEMINI PARA: %s",
            candidate.title,
        )
        raise

    logger.info(
        "DECISÃO EDITORIAL | topic=%s | decision=%s | score=%d",
        candidate.title,
        decision.decision,
        decision.relevance_score,
    )

    return decision


async def judge_topic_bounded(
    persona: Persona,
    candidate: TopicCandidate,
    recent_published_titles: list[str],
) -> EditorialDecision:
    async with _editorial_semaphore:
        return await judge_topic(persona, candidate, recent_published_titles)