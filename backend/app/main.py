"""
Ponto de entrada da aplicação. Responsabilidades:
- criar as tabelas da BD no arranque
- arrancar/parar o AsyncIOScheduler no mesmo event loop do servidor HTTP
- registar os routers da API

Corre com: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from dotenv import load_dotenv

# 1. Carrega as variáveis de ambiente do ficheiro .env antes de importar os módulos que as utilizam
load_dotenv()

# 2. Configura o logging global para nível INFO para vermos os ciclos do agente no terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_feed import router as feed_router
from app.api.routes_init import router as init_router
from app.scheduling.scheduler import shutdown_scheduler, start_scheduler
from app.storage.db import dispose_engine, init_db

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # startup
    logger.info("A inicializar base de dados e agendador...")
    await init_db()
    start_scheduler()
    yield
    # shutdown
    logger.info("A encerrar agendador e conexões...")
    shutdown_scheduler()
    await dispose_engine()


app = FastAPI(
    title="Autonomous AI Persona Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(init_router)
app.include_router(feed_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}