
## 1. Visão Geral da Arquitetura

O projeto adota uma **Clean Architecture** simplificada e modular, garantindo a separação estrita de responsabilidades:
* **Camada de Apresentação (API):** Rotas construídas em FastAPI que expõem os contratos exigidos pelo avaliador (`/api/agent/init` e `/api/agent/feed`).
* **Camada de Orquestração & Ciclo (Core):** O cérebro do agente. Gere a descoberta web, a avaliação crítica editorial, a geração de texto via LLM e o agendamento temporal assíncrono.
* **Camada de Persistência (Storage):** Base de dados SQLite assíncrona utilizando `aiosqlite` em modo **WAL (Write-Ahead Logging)**, garantindo transações atómicas seguras e leitura/escrita concorrente sem bloqueios.

---

## 2. Mapa de Ficheiros e Responsabilidades (`app/`)

```text
app/
├── api/
│   ├── routes_init.py     # Endpoint POST /api/agent/init (cria agente e dispara scheduler)
│   └── routes_feed.py     # Endpoint GET /api/agent/feed (devolve posts por ordem cronológica reversa)
├── core/
│   ├── agent_cycle.py     # Orquestrador central do ciclo autónomo (Discovery ➔ Editorial ➔ Writer ➔ Persist)
│   ├── discovery.py       # Coleta assíncrona de dados externos (RSS, Hacker News, arXiv)
│   ├── editorial.py       # Julgamento crítico estruturado via Pydantic (aprovação/rejeição)
│   ├── persona.py         # Definição imutável da identidade, tom e diretrizes editoriais da IA
│   └── writer.py          # Geração do post final, rationale e rastreio de fontes
├── scheduling/
│   └── scheduler.py       # Gestão do APScheduler (AsyncIOScheduler) para background contínuo
├── schemas/
│   └── api_models.py      # Contratos de dados Pydantic (InitRequest, FeedResponse, PostOut)
└── storage/
    ├── db.py              # Configuração da engine SQLite assíncrona e sessões
    ├── models.py          # Definição das tabelas SQLAlchemy (posts e tópicos vistos)
    └── repository.py      # Camada de CRUD isolada e operações atómicas na BD

```

---

## 3. Como os Módulos e Ficheiros se Comunicam (Fluxo Detalhado)

A regra de ouro da nossa arquitetura é a **unidirecionalidade**: a interface web fala com a camada de API, a API comanda os orquestradores (*Core*), que por sua vez leem e escrevem exclusivamente através da base de dados (*Storage*).

### Passo A: O Ponto de Partida (Inicialização)

1. O avaliador envia o pedido `POST /api/agent/init` para **`app/api/routes_init.py`**.
2. Os dados de entrada são validados pelos modelos Pydantic em **`app/schemas/api_models.py`**.
3. A rota grava o agente na base de dados utilizando **`app/storage/repository.py`** e dispara o agendador em **`app/scheduling/scheduler.py`**.

### Passo B: O Cérebro em Ação (O Ciclo Autónomo)

Assim que o temporizador é acionado, o ficheiro **`app/core/agent_cycle.py`** atua como o maestro que comanda os quatro passos em cadeia:

1. **`discovery.py` (A Pesquisa):** Comunica-se com fontes externas via internet (`httpx` e `feedparser`) para recolher artigos recentes de tecnologia ou IA.
2. **`editorial.py` (O Julgamento):** Recebe os artigos crus, aplica a identidade e regras definidas em **`persona.py`** e utiliza o Pydantic para forçar a IA a tomar uma decisão rigorosa (`publish` ou `reject`) acompanhada de um *rationale* detalhado.
3. **`writer.py` (A Escrita):** Se aprovado, traduz o conteúdo para a voz e tom específicos da persona, formatando o post final e limpando as fontes.
4. **`repository.py` (A Gravação):** O post finalizado é enviado para a camada de armazenamento para ser guardado permanentemente.

### Passo C: A Persistência e a Memória

* **`db.py`** estabelece a ponte assíncrona com o SQLite (`aiosqlite`) ativando o modo **WAL**.
* **`models.py`** define as tabelas estruturadas (histórico de posts e memória de tópicos já vistos para evitar duplicações).
* **`repository.py`** centraliza todas as operações SQL. Nenhum outro módulo escreve diretamente na base de dados, garantindo total isolamento e segurança transacional.

### Passo D: A Entrega ao Consumidor (Leitura do Feed)

1. O avaliador consulta `GET /api/agent/feed?agentId=...` em **`app/api/routes_feed.py`**.
2. A rota valida o parâmetro e chama o **`repository.py`** para ir buscar os posts daquele agente específico ordenados por `created_at DESC` (do mais recente para o mais antigo).
3. Os dados são convertidos para o formato JSON estrito (`FeedResponse` e `PostOut`) e devolvidos ao avaliador.



