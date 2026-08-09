"""
Cliente centralizado para a API do Gemini.

Mantém a mesma interface estruturada utilizada pelo agente:
    - call_claude_structured()
    - call_claude_text()

Internamente utiliza o Google Gen AI SDK (google-genai), com:
    - chamadas verdadeiramente assíncronas (client.aio)
    - rate limiting local (RPM) partilhado por todo o processo
    - retry com exponential backoff + jitter apenas para 429 (quota)
    - erros não retryable (404, 401/403, etc.) propagados de imediato

Configuração através de .env:

    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-2.0-flash
    GEMINI_RPM=15                # opcional, default 15

O modelo nunca é hardcoded como fallback.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional, Type

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logger = logging.getLogger("llm_client")


# ---------------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_RPM = int(os.getenv("GEMINI_RPM", "15"))


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def _validate_configuration() -> None:
    """
    Valida as variáveis necessárias antes de iniciar o cliente.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY não está definida.\n"
            f"Verifica o ficheiro: {ENV_FILE}"
        )

    if not GEMINI_MODEL:
        raise RuntimeError(
            "GEMINI_MODEL não está definida.\n"
            f"Adiciona GEMINI_MODEL ao ficheiro: {ENV_FILE}"
        )

    logger.info(
        "Configuração Gemini carregada | model=%s | rpm=%d | env=%s",
        GEMINI_MODEL,
        GEMINI_RPM,
        ENV_FILE,
    )


# ---------------------------------------------------------------------------
# CLIENT
# ---------------------------------------------------------------------------

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """
    Inicializa e devolve o cliente Gemini.
    """

    global _client

    if _client is not None:
        return _client

    _validate_configuration()

    try:
        _client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        logger.info(
            "Cliente Gemini inicializado com sucesso."
        )

        return _client

    except Exception as exc:
        logger.exception(
            "Erro ao inicializar o cliente Gemini."
        )

        raise RuntimeError(
            "Não foi possível inicializar o cliente Gemini."
        ) from exc


# ---------------------------------------------------------------------------
# MODEL
# ---------------------------------------------------------------------------

def _get_model_name() -> str:
    """
    Devolve exclusivamente o modelo configurado no .env.
    """

    model = os.getenv("GEMINI_MODEL")

    if not model:
        raise RuntimeError(
            "GEMINI_MODEL não está definida no ambiente."
        )

    model = model.strip()

    if model.startswith("models/"):
        model = model.removeprefix("models/")

    return model


# ---------------------------------------------------------------------------
# OPTIONAL MODEL VALIDATION
# ---------------------------------------------------------------------------

def list_available_models() -> list[str]:
    """
    Lista modelos disponíveis para a API key atual.
    """

    client = _get_client()

    try:
        models = client.models.list()

        available = []

        for model in models:
            name = getattr(model, "name", None)

            if not name:
                continue

            name = name.removeprefix("models/")
            available.append(name)

        return sorted(set(available))

    except Exception as exc:
        logger.exception(
            "Não foi possível obter a lista de modelos Gemini."
        )

        raise RuntimeError(
            "Falha ao consultar os modelos disponíveis."
        ) from exc


def validate_configured_model() -> str:
    """
    Verifica se GEMINI_MODEL aparece entre os modelos disponíveis.
    """

    model = _get_model_name()
    available = list_available_models()

    if model not in available:
        raise RuntimeError(
            f"O modelo configurado '{model}' não foi encontrado "
            "entre os modelos disponíveis para esta API key.\n\n"
            "Modelo configurado:\n"
            f"    {model}\n\n"
            "Modelos disponíveis:\n"
            + "\n".join(
                f"    {item}"
                for item in available
            )
        )

    logger.info(
        "Modelo Gemini validado | model=%s",
        model,
    )

    return model


# ---------------------------------------------------------------------------
# ERROR CLASSIFICATION
# ---------------------------------------------------------------------------

class GeminiRateLimitError(RuntimeError):
    """
    429 / RESOURCE_EXHAUSTED (Retryable).
    """

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class GeminiFatalError(RuntimeError):
    """
    404, 401/403 e outros erros não recuperáveis por retry.
    """


def _classify_gemini_error(exc: Exception, model: str) -> Exception:
    """
    Converte uma exceção crua do SDK numa exceção classificada.
    """

    error_text = str(exc)

    if (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "ResourceExhausted" in error_text
    ):
        return GeminiRateLimitError(
            "Quota do Gemini esgotada.\n\n"
            f"Modelo: {model}\n"
            "Erro: 429 RESOURCE_EXHAUSTED\n\n"
            "A chamada será re-tentada automaticamente com backoff."
        )

    if (
        "404" in error_text
        or "NOT_FOUND" in error_text
        or "NotFound" in error_text
    ):
        return GeminiFatalError(
            "Modelo Gemini não encontrado.\n\n"
            f"Modelo configurado: {model}\n\n"
            "Verifica GEMINI_MODEL no .env."
        )

    if (
        "401" in error_text
        or "403" in error_text
        or "PERMISSION_DENIED" in error_text
        or "UNAUTHENTICATED" in error_text
    ):
        return GeminiFatalError(
            "Erro de autenticação/permissão na API Gemini.\n\n"
            "Verifica GEMINI_API_KEY."
        )

    return GeminiFatalError(
        f"Erro na API Gemini | model={model}\n"
        f"{error_text}"
    )


# ---------------------------------------------------------------------------
# RATE LIMITER LOCAL (RPM)
# ---------------------------------------------------------------------------

class _AsyncRateLimiter:
    """
    Sliding-window rate limiter assíncrono.
    """

    def __init__(self, rpm: int):
        self.rpm = rpm
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self._timestamps = [t for t in self._timestamps if now - t < 60]

            while len(self._timestamps) >= self.rpm:
                sleep_for = 60 - (now - self._timestamps[0])
                await asyncio.sleep(max(sleep_for, 0.05))
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if now - t < 60]

            self._timestamps.append(now)


_rate_limiter = _AsyncRateLimiter(rpm=GEMINI_RPM)


# ---------------------------------------------------------------------------
# CHAMADA BASE
# ---------------------------------------------------------------------------

@retry(
    retry=retry_if_exception_type(GeminiRateLimitError),
    wait=wait_exponential_jitter(initial=3, max=60, jitter=3),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _generate(
    model: str,
    contents: str,
    config: types.GenerateContentConfig,
):
    """
    Ponto único de chamada ao Gemini com rate limiting e retries.
    """

    client = _get_client()

    await _rate_limiter.acquire()

    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        return response

    except Exception as exc:
        raise _classify_gemini_error(exc, model) from exc


# ---------------------------------------------------------------------------
# STRUCTURED
# ---------------------------------------------------------------------------

async def call_claude_structured(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2048,
    response_schema: Optional[Type[BaseModel] | Any] = None,
) -> str:
    """
    Gera uma resposta estruturada em JSON.

    Permite passar opcionalmente uma classe Pydantic em `response_schema`
    para forçar o Gemini a responder rigorosamente conforme a estrutura.
    """

    model = _get_model_name()

    logger.info(
        "A chamar Gemini | model=%s | mode=structured",
        model,
    )

    config_kwargs = {
        "system_instruction": system_prompt,
        "max_output_tokens": max_tokens,
        "response_mime_type": "application/json",
    }

    if response_schema is not None:
        config_kwargs["response_schema"] = response_schema

    try:
        response = await _generate(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        text = (response.text or "").strip()

    except GeminiFatalError:
        logger.exception(
            "Erro fatal na chamada estruturada ao Gemini | model=%s",
            model,
        )
        raise

    except GeminiRateLimitError:
        logger.exception(
            "Quota esgotada de forma persistente (após retries) | model=%s",
            model,
        )
        raise

    if not text:
        raise RuntimeError(
            "Gemini devolveu uma resposta estruturada vazia."
        )

    logger.info(
        "Gemini respondeu | model=%s | caracteres=%d",
        model,
        len(text),
    )

    return text


# ---------------------------------------------------------------------------
# TEXT
# ---------------------------------------------------------------------------

async def call_claude_text(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
) -> str:
    """
    Gera uma resposta textual normal.
    """

    model = _get_model_name()

    logger.info(
        "A chamar Gemini | model=%s | mode=text",
        model,
    )

    try:
        response = await _generate(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            ),
        )

        text = (response.text or "").strip()

    except GeminiFatalError:
        logger.exception(
            "Erro fatal na chamada de texto ao Gemini | model=%s",
            model,
        )
        raise

    except GeminiRateLimitError:
        logger.exception(
            "Quota esgotada de forma persistente (após retries) | model=%s",
            model,
        )
        raise

    if not text:
        raise RuntimeError(
            "Gemini devolveu uma resposta vazia."
        )

    logger.info(
        "Gemini respondeu | model=%s | caracteres=%d",
        model,
        len(text),
    )

    return text


# ---------------------------------------------------------------------------
# DIAGNOSTICS
# ---------------------------------------------------------------------------

def get_gemini_status() -> dict:
    """
    Retorna informações de diagnóstico sem expor a API key.
    """

    return {
        "provider": "google-gemini",
        "sdk": "google-genai",
        "model": _get_model_name(),
        "rpm_limit": GEMINI_RPM,
        "env_file": str(ENV_FILE),
        "api_key_configured": bool(GEMINI_API_KEY),
    }