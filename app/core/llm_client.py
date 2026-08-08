"""
Cliente centralizado para a API da Anthropic.

Todos os módulos que precisam do Claude passam por este ficheiro.
"""

from __future__ import annotations

import logging
import os

from anthropic import AsyncAnthropic


logger = logging.getLogger("llm_client")


_client: AsyncAnthropic | None = None


# ---------------------------------------------------------------------------
# MODEL
# ---------------------------------------------------------------------------

def _get_model_name() -> str:

    model = os.environ.get(
        "ANTHROPIC_MODEL"
    )

    if not model:
        raise RuntimeError(
            "ANTHROPIC_MODEL não está definida. "
            "Adiciona um modelo válido ao ficheiro .env."
        )

    return model.strip()


# ---------------------------------------------------------------------------
# CLIENT
# ---------------------------------------------------------------------------

def _get_client() -> AsyncAnthropic:

    global _client

    if _client is not None:
        return _client

    api_key = os.environ.get(
        "ANTHROPIC_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não está definida. "
            "Confirma o ficheiro .env."
        )

    _client = AsyncAnthropic(
        api_key=api_key
    )

    logger.info(
        "Cliente Anthropic inicializado."
    )

    return _client


# ---------------------------------------------------------------------------
# STRUCTURED
# ---------------------------------------------------------------------------

async def call_claude_structured(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
) -> str:

    client = _get_client()
    model = _get_model_name()

    logger.info(
        "A chamar Claude | model=%s | mode=structured",
        model,
    )

    try:

        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

    except Exception:

        logger.exception(
            "Erro na chamada estruturada ao Claude | model=%s",
            model,
        )

        raise

    text_blocks = [
        block.text
        for block in response.content
        if block.type == "text"
    ]

    text = "".join(
        text_blocks
    ).strip()

    if not text:
        raise RuntimeError(
            "Claude devolveu uma resposta vazia."
        )

    logger.info(
        "Claude respondeu | caracteres=%d",
        len(text),
    )

    return text


# ---------------------------------------------------------------------------
# TEXT
# ---------------------------------------------------------------------------

async def call_claude_text(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 600,
) -> str:

    client = _get_client()
    model = _get_model_name()

    logger.info(
        "A chamar Claude | model=%s | mode=text",
        model,
    )

    try:

        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        )

    except Exception:

        logger.exception(
            "Erro na chamada de texto ao Claude | model=%s",
            model,
        )

        raise

    text_blocks = [
        block.text
        for block in response.content
        if block.type == "text"
    ]

    text = "".join(
        text_blocks
    ).strip()

    if not text:
        raise RuntimeError(
            "Claude devolveu uma resposta vazia."
        )

    logger.info(
        "Claude respondeu | caracteres=%d",
        len(text),
    )

    return text

