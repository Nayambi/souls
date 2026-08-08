
"""
Cliente centralizado para a API do Gemini.

Mantém a mesma interface estruturada utilizada pelo agente:
    - call_claude_structured()
    - call_claude_text()

Internamente utiliza o Google Gen AI SDK (google-genai).

Configuração através de .env:

    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-2.0-flash

O modelo nunca é hardcoded como fallback.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logger = logging.getLogger("llm_client")


# ---------------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------------

# Procura o .env a partir da raiz do projeto.
#
# Estrutura esperada:
#
# souls/
# ├── .env
# ├── app/
# │   └── core/
# │       └── llm_client.py
#
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

# override=True garante que o valor do .env substitui uma variável
# GEMINI_MODEL antiga que eventualmente esteja definida no Windows.
load_dotenv(ENV_FILE, override=True)


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")


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
        "Configuração Gemini carregada | model=%s | env=%s",
        GEMINI_MODEL,
        ENV_FILE,
    )


# ---------------------------------------------------------------------------
# CLIENT
# ---------------------------------------------------------------------------

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """
    Inicializa e devolve o cliente Gemini.

    O cliente é criado apenas uma vez.
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

    Não existem modelos hardcoded de fallback.

    Exemplo:

        GEMINI_MODEL=gemini-2.0-flash

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

    Retorna apenas modelos que suportam generateContent.

    Esta função é útil para diagnóstico e não é chamada
    automaticamente em cada request.
    """

    client = _get_client()

    try:
        models = client.models.list()

        available = []

        for model in models:
            name = getattr(model, "name", None)

            if not name:
                continue

            # Normaliza:
            # models/gemini-2.0-flash
            # ->
            # gemini-2.0-flash
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

    Não altera automaticamente o modelo.

    Retorna o modelo configurado quando válido.
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
# ERROR HANDLING
# ---------------------------------------------------------------------------

def _raise_gemini_error(exc: Exception, model: str) -> None:
    """
    Converte erros da API em mensagens mais úteis para o Souls.
    """

    error_text = str(exc)

    # ---------------------------------------------------------------
    # 429 - QUOTA / RESOURCE EXHAUSTED
    # ---------------------------------------------------------------

    if (
        "429" in error_text
        or "RESOURCE_EXHAUSTED" in error_text
        or "ResourceExhausted" in error_text
    ):
        raise RuntimeError(
            "Quota do Gemini esgotada.\n\n"
            f"Modelo: {model}\n"
            "Erro: 429 RESOURCE_EXHAUSTED\n\n"
            "Isto não significa necessariamente que o modelo "
            "deixou de existir. Significa que a quota disponível "
            "para esta API key/modelo foi atingida.\n\n"
            "Altera GEMINI_MODEL no .env para outro modelo "
            "disponível ou aguarda a reposição da quota."
        ) from exc

    # ---------------------------------------------------------------
    # 404 - MODEL NOT FOUND
    # ---------------------------------------------------------------

    if (
        "404" in error_text
        or "NOT_FOUND" in error_text
        or "NotFound" in error_text
    ):
        raise RuntimeError(
            "Modelo Gemini não encontrado.\n\n"
            f"Modelo configurado: {model}\n\n"
            "Verifica GEMINI_MODEL no .env."
        ) from exc

    # ---------------------------------------------------------------
    # 401 / 403 - AUTHENTICATION
    # ---------------------------------------------------------------

    if (
        "401" in error_text
        or "403" in error_text
        or "PERMISSION_DENIED" in error_text
        or "UNAUTHENTICATED" in error_text
    ):
        raise RuntimeError(
            "Erro de autenticação/permissão na API Gemini.\n\n"
            "Verifica GEMINI_API_KEY."
        ) from exc

    # ---------------------------------------------------------------
    # OTHER
    # ---------------------------------------------------------------

    raise RuntimeError(
        f"Erro na API Gemini | model={model}\n"
        f"{error_text}"
    ) from exc


# ---------------------------------------------------------------------------
# STRUCTURED
# ---------------------------------------------------------------------------

async def call_claude_structured(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
) -> str:
    """
    Gera uma resposta estruturada em JSON.

    Mantém o nome antigo 'call_claude_structured'
    para preservar compatibilidade com o agente.
    """

    client = _get_client()
    model = _get_model_name()

    logger.info(
        "A chamar Gemini | model=%s | mode=structured",
        model,
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            ),
        )

        text = (response.text or "").strip()

    except Exception as exc:
        logger.exception(
            "Erro na chamada estruturada ao Gemini | model=%s",
            model,
        )

        _raise_gemini_error(exc, model)
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
    max_tokens: int = 600,
) -> str:
    """
    Gera uma resposta textual normal.

    Mantém o nome antigo 'call_claude_text'
    para preservar compatibilidade com o agente.
    """

    client = _get_client()
    model = _get_model_name()

    logger.info(
        "A chamar Gemini | model=%s | mode=text",
        model,
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
            ),
        )

        text = (response.text or "").strip()

    except Exception as exc:
        logger.exception(
            "Erro na chamada de texto ao Gemini | model=%s",
            model,
        )

        _raise_gemini_error(exc, model)
        raise

    if not text:
        raise RuntimeError(
            "Gemini devolveu uma resposta vazia."
        )

    logger.info(
        "Gemini respondeu | model=%s | caracteres=%d",
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
        "env_file": str(ENV_FILE),
        "api_key_configured": bool(GEMINI_API_KEY),
    }

