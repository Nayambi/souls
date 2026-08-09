
"""
Descoberta de tópicos a partir de fontes externas.

Fontes:
- Simon Willison
- Schneier
- arXiv CS.CR
- arXiv CS.AI
- Hacker News

Este módulo apenas descobre e normaliza tópicos.
A decisão editorial é feita posteriormente pelo LLM.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass

import feedparser
import httpx


logger = logging.getLogger("discovery")


RSS_SOURCES: list[str] = [
    "https://simonwillison.net/atom/everything/",
    "https://www.schneier.com/feed/atom/",
    "https://export.arxiv.org/rss/cs.CR",
    "https://export.arxiv.org/rss/cs.AI",
]


HN_TOPSTORIES_URL = (
    "https://hacker-news.firebaseio.com/v0/topstories.json"
)

HN_ITEM_URL = (
    "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
)


HTTP_TIMEOUT = httpx.Timeout(
    10.0,
    connect=5.0,
)


# ---------------------------------------------------------------------------
# MODEL
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class TopicCandidate:
    title: str
    summary: str
    url: str
    source_name: str

    @property
    def topic_key(self) -> str:
        normalized = re.sub(
            r"[^a-z0-9 ]",
            "",
            self.title.lower(),
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()[:24]


# ---------------------------------------------------------------------------
# RSS
# ---------------------------------------------------------------------------

async def _fetch_rss(
    client: httpx.AsyncClient,
    url: str,
) -> list[TopicCandidate]:

    candidates: list[TopicCandidate] = []

    logger.info(
        "A consultar RSS: %s",
        url,
    )

    try:

        response = await client.get(
            url,
            headers={
                "User-Agent": (
                    "autonomous-persona-agent/1.0"
                )
            },
        )

        response.raise_for_status()

    except httpx.HTTPError as exc:

        logger.warning(
            "Falha HTTP no RSS %s: %s",
            url,
            exc,
        )

        return candidates

    except Exception:

        logger.exception(
            "Erro inesperado ao consultar RSS %s",
            url,
        )

        return candidates

    try:

        parsed = feedparser.parse(
            response.text
        )

        source_name = parsed.feed.get(
            "title",
            url,
        )

        for entry in parsed.entries[:10]:

            title = entry.get(
                "title",
                "",
            ).strip()

            link = entry.get(
                "link",
                "",
            ).strip()

            summary = re.sub(
                r"<[^>]+>",
                "",
                entry.get(
                    "summary",
                    "",
                ),
            ).strip()

            if not title or not link:
                continue

            candidates.append(
                TopicCandidate(
                    title=title,
                    summary=summary[:800],
                    url=link,
                    source_name=source_name,
                )
            )

        logger.info(
            "RSS OK | fonte=%s | candidatos=%d",
            source_name,
            len(candidates),
        )

    except Exception:

        logger.exception(
            "Erro ao processar RSS %s",
            url,
        )

    return candidates


# ---------------------------------------------------------------------------
# HACKER NEWS
# ---------------------------------------------------------------------------

async def _fetch_hackernews(
    client: httpx.AsyncClient,
    limit: int = 15,
) -> list[TopicCandidate]:

    candidates: list[TopicCandidate] = []

    logger.info(
        "A consultar Hacker News..."
    )

    try:

        response = await client.get(
            HN_TOPSTORIES_URL
        )

        response.raise_for_status()

        story_ids: list[int] = (
            response.json()[:limit]
        )

        logger.info(
            "Hacker News: %d stories encontradas.",
            len(story_ids),
        )

    except httpx.HTTPError as exc:

        logger.warning(
            "Falha HTTP no Hacker News: %s",
            exc,
        )

        return candidates

    except (ValueError, TypeError) as exc:

        logger.warning(
            "Resposta inválida do Hacker News: %s",
            exc,
        )

        return candidates

    except Exception:

        logger.exception(
            "Erro inesperado ao consultar Hacker News."
        )

        return candidates

    for story_id in story_ids:

        try:

            item_resp = await client.get(
                HN_ITEM_URL.format(
                    item_id=story_id
                )
            )

            item_resp.raise_for_status()

            item = item_resp.json()

        except httpx.HTTPError as exc:

            logger.warning(
                "Falha ao obter HN item %s: %s",
                story_id,
                exc,
            )

            continue

        except (ValueError, TypeError) as exc:

            logger.warning(
                "JSON inválido no HN item %s: %s",
                story_id,
                exc,
            )

            continue

        title = (
            (item or {})
            .get("title", "")
            .strip()
        )

        url = (
            (item or {})
            .get("url", "")
            .strip()
        )

        if not title or not url:
            continue

        if not _looks_ai_or_security_related(
            title
        ):
            continue

        candidates.append(
            TopicCandidate(
                title=title,
                summary=(
                    "Discussão na Hacker News "
                    f"com {(item or {}).get('score', 0)} pontos."
                ),
                url=url,
                source_name="Hacker News",
            )
        )

    logger.info(
        "Hacker News OK | candidatos relevantes=%d",
        len(candidates),
    )

    return candidates


# ---------------------------------------------------------------------------
# RELEVÂNCIA
# ---------------------------------------------------------------------------

_KEYWORDS = (
    "ai",
    "artificial intelligence",
    "llm",
    "machine learning",
    "model",
    "gpt",
    "claude",
    "gemini",
    "neural",
    "security",
    "vulnerability",
    "exploit",
    "prompt",
    "agent",
    "open source",
    "inference",
    "training",
)


def _looks_ai_or_security_related(
    title: str,
) -> bool:

    lowered = title.lower()

    return any(
        keyword in lowered
        for keyword in _KEYWORDS
    )


# ---------------------------------------------------------------------------
# DISCOVERY PRINCIPAL
# ---------------------------------------------------------------------------

async def discover_topics() -> list[TopicCandidate]:

    logger.info(
        "========== DISCOVERY START =========="
    )

    async with httpx.AsyncClient(
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
    ) as client:

        rss_tasks = [
            _fetch_rss(
                client,
                url,
            )
            for url in RSS_SOURCES
        ]

        rss_results, hn_results = await asyncio.gather(
            asyncio.gather(
                *rss_tasks
            ),
            _fetch_hackernews(
                client
            ),
        )

    all_candidates = (
        [
            candidate
            for batch in rss_results
            for candidate in batch
        ]
        + hn_results
    )

    logger.info(
        "Discovery bruto | candidatos=%d",
        len(all_candidates),
    )

    # ---------------------------------------------------------
    # DEDUPLICAÇÃO
    # ---------------------------------------------------------

    seen_keys: set[str] = set()

    deduped: list[TopicCandidate] = []

    for candidate in all_candidates:

        if candidate.topic_key in seen_keys:
            continue

        seen_keys.add(
            candidate.topic_key
        )

        deduped.append(
            candidate
        )

    logger.info(
        "Discovery final | candidatos=%d",
        len(deduped),
    )

    logger.info(
        "========== DISCOVERY END =========="
    )

    return deduped

