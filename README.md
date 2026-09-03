# Swipe

A writing-integrity platform: upload a document, get it back as a marked-up
manuscript showing passages that match known sources and (from Phase 1) sentences
that show signs of AI generation.

This repository is being built in phases. **You are at Phase 0** — the foundation:
project structure, database schema via migrations, and a working similarity engine
behind a FastAPI backend. See `docs/08-roadmap.md` for what comes next.

## Layout

```
api/     FastAPI backend, similarity engine, migrations, tests
web/     React frontend (Phase 3 — placeholder for now)
infra/   deployment files (Phase 5)
corpus/  sample reference documents to index
docs/    the full product & system blueprint (00–08) + wireframes
```

## Quick start

Requires Docker (for Postgres) and Python 3.11+.

```bash
cp .env.example api/.env
docker compose up -d                 # postgres, redis, minio
cd api
pip install -e ".[dev]"
alembic upgrade head                 # create tables
python scripts/seed_corpus.py        # load corpus/ as sources
python -m pytest -q                  # 6 passing
uvicorn app.main:app --reload        # http://localhost:8000/docs
```

Or just `make dev` from the repo root, which does all of the above.

No Docker? Use SQLite: `echo 'DATABASE_URL=sqlite:///./dev.db' > api/.env`, then
the same `alembic`/`pytest`/`uvicorn` steps.

## Try it

Open http://localhost:8000/docs and use:
- `POST /api/v1/sources` — add a reference document
- `POST /api/v1/checks` — upload a .docx/.pdf/.txt to check
- `POST /api/v1/checks/text` — check pasted text
- `GET  /api/v1/checks/{id}` — fetch a stored report

## Docs

The complete blueprint (architecture, schema, API, detection, frontend,
deployment, roadmap) is in `docs/`. Start with `docs/00-overview.md`.
