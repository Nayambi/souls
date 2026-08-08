"""
Engine e sessão assíncronos partilhados por toda a aplicação.

Usa uma única AsyncEngine (evita conexões soltas) e ativa WAL mode no
SQLite para permitir leitores concorrentes (GET /feed) enquanto o
scheduler escreve em background, sem lock mútuo.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.storage.models import Base

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "agent.db"

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

_engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@event.listens_for(_engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
    """Ativa WAL mode e foreign keys em cada nova conexão física."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=5000;")
    cursor.close()


async def init_db() -> None:
    """Cria as tabelas se ainda não existirem. Chamado no lifespan do FastAPI."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager de sessão — cada unidade de trabalho abre/fecha a sua própria."""
    async with _session_factory() as session:
        yield session


async def dispose_engine() -> None:
    await _engine.dispose()
