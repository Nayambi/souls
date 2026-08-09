"""Fixtures partilhadas — BD isolada por sessão de testes."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Tem de correr antes de qualquer import de app.* nos módulos de teste.
_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="souls_pytest_"))
os.environ.setdefault("AGENT_DB_PATH", str(_TEST_DATA_DIR / "agent.db"))
os.environ.setdefault("SCHEDULER_DB_PATH", str(_TEST_DATA_DIR / "scheduler.db"))


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """
    Cliente HTTP contra a app FastAPI.

    NOTA: httpx.ASGITransport não dispara os eventos de lifespan do ASGI
    (startup/shutdown) — só encaminha pedidos HTTP. Por isso init_db() é
    chamado aqui explicitamente, em vez de depender do lifespan da app
    (que só corre de facto sob uvicorn) para garantir que as tabelas
    existem antes de qualquer teste bater no endpoint /init.
    """
    from app.main import app
    from app.storage.db import init_db

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
