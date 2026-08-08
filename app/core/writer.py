"""
Gera o texto final do post, grounded estritamente no conteúdo já
recolhido pelo discovery (nunca deixa o modelo "completar de memória"
uma fonte que não leu). Produz também o rationale estruturado exigido
pela API (why selected, why relevant now, sources).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.discovery import TopicCandidate
from app.core.editorial import EditorialDecision
from app.core.llm_client import call_claude_text
from app.core.persona import Persona

WRITER_SYSTEM_TEMPLATE = """{persona_block}

Vais agora escrever um post curto (estilo post de rede social profissional,
tipo thread inicial no X/LinkedIn) sobre o tópico fornecido. Regras:
- Usa APENAS a informação fornecida no resumo/contexto abaixo. Não inventes
  factos, números ou citações que não estão presentes na fonte.
- Mantém o teu tom e as tuas posições editoriais definidas acima.
- Entre 400 e 800 caracteres. Sem hashtags em excesso, sem emojis.
- Termina com uma opinião ou ângulo claro teu, não apenas um resumo neutro.
- Não menciones que és uma IA."""

WRITER_USER_TEMPLATE = """Tópico aprovado para publicação:
Título: {title}
Resumo/contexto (única fonte de factos permitida): {summary}
Fonte: {source_name} ({url})

Por que foi selecionado (usa isto para calibrar o ângulo do post):
{editorial_reasoning}

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


async def write_post(
    persona: Persona,
    candidate: TopicCandidate,
    decision: EditorialDecision,
) -> WrittenPost:
    system_prompt = WRITER_SYSTEM_TEMPLATE.format(persona_block=persona.system_prompt_block())
    user_prompt = WRITER_USER_TEMPLATE.format(
        title=candidate.title,
        summary=candidate.summary or "(sem resumo disponível, baseia-te apenas no título)",
        source_name=candidate.source_name,
        url=candidate.url,
        editorial_reasoning=decision.reasoning,
    )

    text = await call_claude_text(system_prompt=system_prompt, user_prompt=user_prompt)

    return WrittenPost(
        text=text,
        rationale=_build_rationale(candidate, decision),
        sources=[candidate.url],
    )
