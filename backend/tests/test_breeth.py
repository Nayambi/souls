"""
Testes do módulo app.core.breeth. Não fazem nenhuma chamada de rede real —
o httpx.AsyncClient é substituído por um dublê (fake) controlado em cada
teste, para validar o comportamento sem gastar chamadas à API do Breeth.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx
import pytest

from app.core import breeth


@dataclass
class _FakeCandidate:
    """Imita um TopicCandidate real — só precisamos do atributo .title."""
    title: str


class _FakeResponse:
    """Imita httpx.Response o suficiente para os nossos fins."""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("erro fake", request=None, response=self)

    def json(self) -> dict:
        return self._json_data


class _FakeAsyncClient:
    """
    Imita httpx.AsyncClient como context manager assíncrono.
    `responder` é uma função (url, json_payload) -> _FakeResponse | levanta exceção,
    definida por cada teste conforme o cenário que quer simular.
    """

    def __init__(self, responder):
        self._responder = responder
        self.calls: list[tuple[str, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, url, headers=None, json=None, **kwargs):
        self.calls.append((url, json))
        return self._responder(url, json)


def _patch_client(monkeypatch, responder):
    """Substitui httpx.AsyncClient por um fake que usa `responder` para cada POST."""
    fake_client_holder: dict = {}

    def factory(*args, **kwargs):
        client = _FakeAsyncClient(responder)
        fake_client_holder["client"] = client
        return client

    monkeypatch.setattr(breeth.httpx, "AsyncClient", factory)
    return fake_client_holder


# ---------------------------------------------------------------------------
# search_similar_context(persona, candidates)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_sem_api_key_devolve_lista_vazia(monkeypatch):
    """Sem BREETH_API_KEY configurada, não deve tentar chamar a rede."""
    monkeypatch.setattr(breeth, "BREETH_API_KEY", None)

    def responder(url, payload):
        raise AssertionError("não devia chamar a rede sem API key")

    _patch_client(monkeypatch, responder)

    candidates = [_FakeCandidate(title="IA generativa em saúde")]
    result = await breeth.search_similar_context(persona=None, candidates=candidates)
    assert result == []


@pytest.mark.asyncio
async def test_search_devolve_narrativas_dos_episodios(monkeypatch):
    """Caso feliz: a query é montada a partir dos títulos e as narrativas voltam tal
    como o Breeth as devolveu (esta versão do breeth.py não filtra vazias)."""
    monkeypatch.setattr(breeth, "BREETH_API_KEY", "fake-key")

    def responder(url, payload):
        assert url.endswith("/search")
        assert "IA generativa em saúde" in payload["query"]
        return _FakeResponse({
            "results": [
                {"narrative": "Já publicámos sobre IA generativa em diagnóstico médico."},
                {"narrative": "Post anterior sobre regulação de IA na saúde."},
            ]
        })

    _patch_client(monkeypatch, responder)

    candidates = [_FakeCandidate(title="IA generativa em saúde")]
    result = await breeth.search_similar_context(persona=None, candidates=candidates)
    assert result == [
        "Já publicámos sobre IA generativa em diagnóstico médico.",
        "Post anterior sobre regulação de IA na saúde.",
    ]


@pytest.mark.asyncio
async def test_search_usa_no_maximo_5_titulos_na_query(monkeypatch):
    """candidates[:5] — confirma que só os primeiros 5 títulos entram na query,
    mesmo que a lista de candidatos seja maior."""
    monkeypatch.setattr(breeth, "BREETH_API_KEY", "fake-key")
    captured = {}

    def responder(url, payload):
        captured["query"] = payload["query"]
        return _FakeResponse({"results": []})

    _patch_client(monkeypatch, responder)

    candidates = [_FakeCandidate(title=f"Tópico {i}") for i in range(8)]
    await breeth.search_similar_context(persona=None, candidates=candidates)

    assert "Tópico 5" not in captured["query"]
    assert "Tópico 4" in captured["query"]


@pytest.mark.asyncio
async def test_search_com_erro_http_falha_aberta(monkeypatch):
    """Se o Breeth responder com erro, o ciclo não deve quebrar — devolve []."""
    monkeypatch.setattr(breeth, "BREETH_API_KEY", "fake-key")

    def responder(url, payload):
        return _FakeResponse({}, status_code=500)

    _patch_client(monkeypatch, responder)

    candidates = [_FakeCandidate(title="algum tópico")]
    result = await breeth.search_similar_context(persona=None, candidates=candidates)
    assert result == []


# ---------------------------------------------------------------------------
# record_publication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_publication_envia_payload_correto(monkeypatch):
    """Confirma o formato exato enviado a /episodes (role/content, rationale, fontes)."""
    monkeypatch.setattr(breeth, "BREETH_API_KEY", "fake-key")
    captured = {}

    def responder(url, payload):
        assert url.endswith("/episodes")
        captured["payload"] = payload
        return _FakeResponse({"id": "ep_123"})

    _patch_client(monkeypatch, responder)

    await breeth.record_publication(
        agent_id="agent_1",
        topic_title="LLMs aplicados a diagnóstico médico",
        rationale="Timing forte: lançamento recente de um modelo especializado.",
        sources=["https://exemplo.com/artigo"],
    )

    messages = captured["payload"]["messages"]
    assert messages[0]["role"] == "user"
    assert "LLMs aplicados a diagnóstico médico" in messages[0]["content"]
    assert messages[1]["role"] == "assistant"
    assert "Timing forte" in messages[1]["content"]
    assert "https://exemplo.com/artigo" in messages[1]["content"]


@pytest.mark.asyncio
async def test_record_publication_com_erro_nao_levanta_excecao(monkeypatch):
    """Uma falha ao gravar o episódio não deve propagar — o post já foi salvo antes."""
    monkeypatch.setattr(breeth, "BREETH_API_KEY", "fake-key")

    def responder(url, payload):
        return _FakeResponse({}, status_code=503)

    _patch_client(monkeypatch, responder)

    # não deve levantar exceção
    await breeth.record_publication(
        agent_id="agent_1",
        topic_title="qualquer tópico",
        rationale="qualquer rationale",
        sources=[],
    )