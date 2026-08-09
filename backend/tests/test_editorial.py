"""
Testa o schema EditorialDecision isoladamente, sem chamar o modelo nem
a rede — valida apenas que a estrutura força os campos corretos.
Corre com: pytest tests/test_editorial.py
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.editorial import EditorialDecision


def test_valid_decision_parses() -> None:
    decision = EditorialDecision(
        decision="publish",
        reasoning="Tópico alinha com segurança de LLMs e traz detalhe técnico verificável.",
        relevance_score=8,
        matches_persona_interests=True,
        is_duplicate_or_stale=False,
        relevance_now="Divulgação de vulnerabilidade publicada há 2 dias.",
        manifesto_rule="M2 — valoriza mais reprodutibilidade e disclosure responsável do que velocidade de lançamento.",
    )
    assert decision.decision == "publish"
    assert 1 <= decision.relevance_score <= 10


def test_invalid_decision_literal_rejected() -> None:
    with pytest.raises(ValidationError):
        EditorialDecision(
            decision="maybe",  # type: ignore[arg-type]
            reasoning="Justificação com tamanho suficiente para passar a validação mínima.",
            relevance_score=5,
            matches_persona_interests=True,
            is_duplicate_or_stale=False,
            relevance_now="Timing qualquer.",
            manifesto_rule="M1 — cética em relação a anúncios de marketing sem detalhes técnicos verificáveis.",
        )


def test_reasoning_too_short_rejected() -> None:
    with pytest.raises(ValidationError):
        EditorialDecision(
            decision="reject",
            reasoning="curto",
            relevance_score=3,
            matches_persona_interests=False,
            is_duplicate_or_stale=False,
            relevance_now="não relevante",
            manifesto_rule="M1 — cética em relação a anúncios de marketing sem detalhes técnicos verificáveis.",
        )


def test_relevance_score_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        EditorialDecision(
            decision="publish",
            reasoning="Justificação com tamanho suficiente para passar a validação mínima.",
            relevance_score=11,
            matches_persona_interests=True,
            is_duplicate_or_stale=False,
            relevance_now="Timing válido e explicado.",
            manifesto_rule="M3 — prefere analisar mecanismos concretos a especular sobre AGI.",
        )
