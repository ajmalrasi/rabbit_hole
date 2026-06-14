# Rabbit Hole — Backend

> Discover the hidden mechanisms behind ordinary things.
> **"What invisible system is causing this?"**

Rabbit Hole is **not** a news summariser. It ingests articles from curious
corners of the web, scores them for how strongly they point to an *invisible
underlying system* (physics, engineering, biology, economics, …), and turns the
best ones into structured "rabbit holes" that explain the hidden mechanism
behind everyday things.

Examples of the spirit:

| Ordinary thing        | Hidden mechanism                         |
| --------------------- | ---------------------------------------- |
| Football at altitude  | Air density & aerodynamic drag           |
| Tea plantations       | Agricultural optimisation & microclimate |
| Container ships       | Fuel economics & hull hydrodynamics      |
| Airport runways       | Radio navigation systems                 |
| Coconut trees         | Phototropism & wind adaptation           |
| Bridges               | Thermal expansion engineering            |
| Volcanoes             | Electrostatic charge & lightning         |

---

## Architecture

```
backend/
├── app/            # FastAPI app, config, logging
│   ├── main.py       # app factory + lifespan (DB init, scheduler)
│   ├── config.py     # pydantic-settings (all env vars)
│   └── logging_config.py
├── models/         # SQLAlchemy ORM models + Pydantic schemas
├── database/       # engine/session, repositories (repository pattern), init
│   └── repositories/
├── services/       # business logic (service layer)
│   ├── rss_service.py
│   ├── curiosity_service.py
│   ├── rabbit_hole_service.py
│   ├── embedding_service.py
│   ├── feed_service.py
│   └── llm/          # LLM abstraction (Ollama / OpenAI / Gemini)
├── prompts/        # prompt templates
├── api/            # HTTP routers + dependency injection wiring
│   └── routes/
├── jobs/           # APScheduler + end-to-end pipeline
├── tests/          # unit tests (run without Postgres / LLM)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### Pipeline

```
RSS feeds ─▶ ingest ─▶ curiosity scoring ─▶ gate ─▶ rabbit-hole generation
                                                       │
                                            embedding + near-dup check
                                                       │
                                                  daily feed ranking
```

Each stage is a service; the `jobs/pipeline.py` orchestrator wires them together
and is driven by APScheduler (`jobs/scheduler.py`) or the admin API.

---

## Quick start (Docker, on the Jetson Orin Nano)

The stack targets a **Jetson Orin Nano at `192.168.3.30`**. Both images
(`pgvector/pgvector:pg16` and `python:3.12-slim`) are multi-arch and pull their
`linux/arm64` variants automatically.

```bash
cd backend
cp .env.example .env
# edit .env: set passwords, choose LLM_PROVIDER, set OLLAMA_BASE_URL / API keys

docker compose up -d --build
```

The API is then available at `http://192.168.3.30:8000` with interactive docs at
`http://192.168.3.30:8000/docs`.

### Using local Ollama on the Jetson

If Ollama runs on the Jetson host itself:

```bash
# pull the models you reference in .env
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

In `.env`, point the backend at the host. Either works:

```ini
OLLAMA_BASE_URL=http://192.168.3.30:11434      # LAN address of the Jetson
# or, since compose adds host-gateway:
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

> **Important:** `EMBEDDING_DIM` must match your embedding model.
> `nomic-embed-text` and `text-embedding-004` → `768`,
> `text-embedding-3-small` → `1536`. If you change the embedding model after
> data already exists, recreate the `rabbit_holes` table (the vector column is
> fixed-dimension).

---

## Configuration

All configuration is via environment variables (see `.env.example`). Highlights:

| Variable                     | Purpose                                          | Default |
| ---------------------------- | ------------------------------------------------ | ------- |
| `LLM_PROVIDER`               | text generation: `ollama` / `openai` / `gemini`  | ollama  |
| `EMBEDDING_PROVIDER`         | embeddings provider                              | ollama  |
| `EMBEDDING_DIM`              | vector size (must match model)                   | 768     |
| `MIN_CURIOSITY_SCORE`        | gate threshold (0–10)                            | 6.0     |
| `MIN_HIDDEN_MECHANISM_SCORE` | gate threshold (0–10)                            | 6.0     |
| `DEDUP_DISTANCE_THRESHOLD`   | cosine distance below which → duplicate           | 0.15    |
| `DAILY_PIPELINE_HOUR`        | hour (UTC) for the once-daily full pipeline      | 6       |
| `DAILY_PIPELINE_MINUTE`      | minute (UTC) for the daily pipeline              | 0       |
| `DAILY_FEED_SIZE`            | items in the daily feed                          | 20      |
| `PIPELINE_DRAIN_ON_PROCESS`  | drain all pending articles on manual `/process`  | true    |
| `RUN_ON_STARTUP`             | run pipeline once after boot                     | false   |

The text and embedding providers are independent — e.g. use local Ollama for
embeddings and remote OpenAI for generation.

---

## REST API

| Method | Path                    | Description                              |
| ------ | ----------------------- | ---------------------------------------- |
| GET    | `/feed`                 | Curated daily feed of rabbit holes       |
| GET    | `/rabbit-hole/{id}`     | A single rabbit hole (full detail)       |
| GET    | `/categories`           | Categories with counts                   |
| GET    | `/search?q=...`         | Semantic (vector) or keyword search      |
| POST   | `/admin/pipeline/run`   | Trigger a full pipeline run (background) |
| POST   | `/admin/feed/rebuild`   | Rebuild the daily feed now               |
| GET    | `/health`               | Liveness + DB/provider status            |

`/search` uses pgvector cosine similarity by default and transparently falls
back to keyword search if the embedding backend is unavailable
(`?semantic=false` forces keyword search).

A rabbit hole has the shape:

```json
{
  "id": 1,
  "title": "...",
  "observation": "...",
  "question": "...",
  "hidden_mechanism": "...",
  "explanation": "...",
  "interesting_fact": "...",
  "why_it_matters": "...",
  "follow_up_question": "...",
  "category": "physics",
  "source_url": "https://...",
  "curiosity_score": 9.0,
  "hidden_mechanism_score": 8.5,
  "created_at": "2026-06-14T06:00:00Z"
}
```

---

## Local development (without Docker)

Requires Python 3.12 and a reachable PostgreSQL with the `vector` extension.

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set POSTGRES_HOST=localhost etc.

uvicorn app.main:app --reload --port 8000
```

### Running tests

The unit tests use in-memory fakes and need **no** database or LLM:

```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## Data sources

Hacker News · Reddit r/technology · Reddit r/todayilearned · IEEE Spectrum ·
NASA · Interesting Engineering · Nature · Science Daily

Add or remove sources in `services/feeds.py`.

---

## Code quality

- **Type hints** throughout, validated domain models with Pydantic v2.
- **Repository pattern** isolates all DB queries (`database/repositories/`).
- **Service layer** holds business logic, independent of the web framework.
- **Dependency injection** via FastAPI `Depends` (`api/deps.py`).
- **Structured logging** configured centrally.
- **Unit tests** for the scoring, generation, dedup, and feed logic.
```
