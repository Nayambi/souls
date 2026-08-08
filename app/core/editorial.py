from __future__ import annotations

import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from app.core.discovery import TopicCandidate
from app.core.persona import Persona
from app.core.llm_client import call_claude_structured


logger = logging.getLogger("editorial")


class EditorialDecision(BaseModel):
    decision: Literal["publish", "reject"]

    reasoning: str = Field(min_length=1)

    relevance_score: int = Field(
        ge=1,
        le=10,
    )

    matches_persona_interests: bool

    is_duplicate_or_stale: bool

    relevance_now: str = Field(min_length=1)


EDITORIAL_SYSTEM_TEMPLATE = """
You are the editorial decision engine of an autonomous AI security
content creator.

PERSONA:
{persona_block}

Your task is to determine whether a discovered topic should become
a post for this persona.

IMPORTANT:
Do NOT be excessively restrictive.

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

For example:

"An AI model hacked another company during testing"

is HIGHLY RELEVANT to an AI security persona because it concerns
an AI model performing an offensive security action.

SCORING:

1-2:
Clearly unrelated to the persona.

3-4:
Weak relationship.

5-6:
Reasonably relevant.

7-8:
Clearly relevant.

9-10:
Extremely relevant and highly important.

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

Do NOT reject merely because the topic is broad.

Return ONLY valid JSON.

Required format:

{{
  "decision": "publish" or "reject",
  "reasoning": "explanation",
  "relevance_score": 1-10,
  "matches_persona_interests": true or false,
  "is_duplicate_or_stale": true or false,
  "relevance_now": "explanation"
}}
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

The question is NOT:
"Does this title exactly match the persona keywords?"

The question is:
"Can this topic produce a technically valuable post for this
AI security audience?"

Return ONLY JSON.
"""


def _clean_json_response(raw: str) -> str:
    """
    Remove markdown code fences and extraneous whitespace.
    """

    text = raw.strip()

    # Remove ```json ... ```
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

    # Caso o modelo tenha colocado texto antes/depois do JSON.
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text


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

    system_prompt = EDITORIAL_SYSTEM_TEMPLATE.format(
        persona_block=persona_block,
    )

    recent_posts = (
        "\n".join(
            f"- {title}"
            for title in recent_published_titles
        )
        if recent_published_titles
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
        raw_response = await call_claude_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    except Exception:
        logger.exception(
            "ERRO AO CHAMAR CLAUDE PARA: %s",
            candidate.title,
        )
        raise

    logger.info(
        "Resposta bruta do Claude para '%s': %s",
        candidate.title,
        raw_response,
    )

    try:
        cleaned = _clean_json_response(
            raw_response
        )

        logger.debug(
            "JSON limpo: %s",
            cleaned,
        )

        data = json.loads(cleaned)

    except Exception:
        logger.exception(
            "ERRO AO FAZER PARSE DO JSON | tópico=%s | resposta=%r",
            candidate.title,
            raw_response,
        )

        raise RuntimeError(
            "Claude devolveu uma resposta que não é JSON válido."
        )

    try:
        decision = EditorialDecision.model_validate(
            data
        )

    except Exception:
        logger.exception(
            "ERRO DE VALIDAÇÃO EditorialDecision | "
            "tópico=%s | data=%r",
            candidate.title,
            data,
        )

        raise

    logger.info(
        "DECISÃO EDITORIAL | topic=%s | decision=%s | score=%d",
        candidate.title,
        decision.decision,
        decision.relevance_score,
    )

    return decision