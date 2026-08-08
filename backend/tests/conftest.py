"""Fixtures partilhadas — BD isolada por sessão de testes."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Tem de correr antes de qualquer import de app.* nos módulos de teste.
_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="souls_pytest_"))
os.environ.setdefault("AGENT_DB_PATH", str(_TEST_DATA_DIR / "agent.db"))
os.environ.setdefault("SCHEDULER_DB_PATH", str(_TEST_DATA_DIR / "scheduler.db"))


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Cliente HTTP contra a app FastAPI (inclui lifespan e init da BD)."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
