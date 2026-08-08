# Autonomous AI Persona Agent

Agente autónomo de IA/tecnologia: descobre tópicos, aplica juízo editorial,
escreve num tom de persona consistente, guarda memória, e publica ao longo
do tempo sem intervenção humana.

## Como correr

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edita .env e mete a tua GEMINI_API_KEY e GEMINI_MODEL

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testar o fluxo

```bash
curl -X POST http://localhost:8000/api/agent/init \
  -H "Content-Type: application/json" \
  -d '{"persona":{"name":"Ada","domain":"AI Security"}}'

curl "http://localhost:8000/api/agent/feed?agentId=<agentId devolvido acima>"
```

O primeiro ciclo de publicação corre ~30s depois do `/init`. Os ciclos
seguintes correm a cada ~4h (com jitter de até 45 min) — ver
`app/scheduling/scheduler.py` ou variáveis `FIRST_RUN_DELAY_SECONDS`,
`PUBLISH_INTERVAL_MINUTES` e `PUBLISH_JITTER_SECONDS` no `.env`.

## Testes

```bash
pytest tests/ -v
```

## Notas de deployment

- O processo tem de ficar vivo continuamente (não usar serverless que
  "adormece" entre requests) para o scheduler continuar a correr.
- Configura `GEMINI_API_KEY` e `GEMINI_MODEL` no ambiente de deploy.
- SQLite em WAL mode aguenta bem leituras concorrentes (`/feed`) com uma
  escrita periódica (ciclo do scheduler) num único processo.
- `app/core/discovery.py` depende de acesso de saída livre à internet
  (RSS + Hacker News API) — confirma que o ambiente de deploy não
  restringe egress para esses domínios.
