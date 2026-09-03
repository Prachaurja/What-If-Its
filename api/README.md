# Swipe API

FastAPI backend. Phase 0 provides the similarity engine and check endpoints;
auth, orgs, the queue, and the AI detector arrive in later phases.

## Structure

    app/
      core/config.py            settings from env
      db/                       SQLAlchemy base + session
      models/                   organisations, users, documents, fingerprints, checks
      services/
        extract.py              docx/pdf/txt -> text
        similarity/             normalise, shingle, winnow, index, match
        report.py               runs a full check (inline now, Celery task later)
      routers/                  health, checks, sources
      main.py                   app factory
    alembic/                    migrations
    scripts/seed_corpus.py      load corpus/ as sources
    tests/                      pytest (SQLite, no Postgres needed)

## Commands

    alembic revision --autogenerate -m "..."   # after changing models
    alembic upgrade head                        # apply
    python -m pytest -q                         # test
    uvicorn app.main:app --reload               # serve

## Notes on the similarity engine

Text -> normalise -> 5-word shingles -> blake2b hash -> winnow (keep the min
hash per 8-hash window) -> fingerprints table. Winnowing guarantees any copied
run of 12+ words shares a fingerprint with its source, at ~1/5 the storage of
keeping every shingle. Candidate sources are found with one GROUP BY over the
fingerprints table; matched passages are then rescored exactly.
