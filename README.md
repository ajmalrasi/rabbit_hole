# Rabbit Hole

Discover the hidden mechanisms behind ordinary things.

> **"What invisible system is causing this?"**

Rabbit Hole is not a news summarizer. It reveals the invisible systems — physics, engineering, biology, economics — that govern everyday observations.

## Repository layout

| Path | Description |
| ---- | ----------- |
| [`backend/`](backend/) | FastAPI backend (RSS ingestion, LLM pipeline, REST API, Docker) |
| Android app | *(planned)* |

## Quick start

See [`backend/README.md`](backend/README.md) for setup on the Jetson Orin Nano (`192.168.3.30`):

```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

API: `http://192.168.3.30:8000` · Docs: `/docs`
