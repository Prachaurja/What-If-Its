# 01 · System architecture

## Components

```
                         ┌────────────────────────────────────────────────────────┐
   browser ──HTTPS──▶    │  Caddy (TLS, static files, reverse proxy)              │
                         └───────────────┬────────────────────────┬───────────────┘
                                         │ /api/*                 │ /*
                                         ▼                        ▼
                         ┌───────────────────────────┐   ┌────────────────────┐
                         │ API  (FastAPI, uvicorn)   │   │ Web (React, built  │
                         │ auth · orgs · checks ·    │   │ static bundle)     │
                         │ sources · billing         │   └────────────────────┘
                         └───────┬───────────┬───────┘
                                 │ enqueue   │ read/write
                                 ▼           ▼
                   ┌──────────────────┐   ┌──────────────────────────────┐
                   │ Redis            │   │ PostgreSQL                   │
                   │ job queue, rate  │   │ accounts · documents ·       │
                   │ limits, cache    │   │ fingerprints · checks · usage│
                   └────────┬─────────┘   └──────────────────────────────┘
                            │ dequeue                    ▲
                            ▼                            │
              ┌─────────────────────────────┐            │
              │ Worker  (Celery)            │────────────┘
              │ extract → fingerprint →     │
              │ local match → web fallback  │──▶ Search API (Brave)  ──▶ web pages
              │ → AI ensemble → save        │
              └─────────────┬───────────────┘
                            │ files, model weights
                            ▼
                   ┌──────────────────┐
                   │ MinIO (S3 API)   │
                   │ uploads · corpus │
                   │ models · exports │
                   └──────────────────┘
```

All seven boxes run as containers on one VPS via docker compose. The Worker box is the only one that needs real CPU/RAM; the AI models run inside it (CPU with quantised weights at first; move to a GPU box later by pointing a second worker at the same Redis).

## Request flow: running a check

```
1  browser   POST /api/checks  (multipart file, options)
2  API       rate-limit ▸ auth ▸ org + role ▸ quota
3  API       store file in MinIO ▸ extract text ▸ insert documents row
             insert checks row status=queued ▸ run_check.delay(id) ▸ 202 {id}
4  browser   GET /api/checks/{id} every 2 s
5  worker    status=running
             a. normalise, shingle, winnow → fingerprints (insert)
             b. local match: fingerprints of this text vs org repo + public corpus
             c. quote/reference exclusion (if option set)
             d. web fallback: distinctive sentences → search → fetch → match → cache
             e. AI ensemble: Binoculars + DeBERTa → stacker → calibrated band
             f. write payload, similarity_pct, ai_prob, check_sources rows
             g. usage.checks_run += 1  ▸ status=done
6  browser   sees status=done ▸ renders manuscript
```

Typical latency: local-only check 1–3 s; with web fallback 5–15 s; with AI ensemble on CPU 20–60 s. The queue means the API responds in <100 ms regardless.

## Request flow: adding reference sources

Bulk upload → each file becomes a `documents` row with `kind=source` and gets fingerprinted by a worker task. Large corpora (Wikipedia) go through `scripts/ingest/` which streams the dump straight into Postgres with COPY, bypassing the API.

## Trust boundaries

- Every query in the API is scoped by `org_id` from the authenticated context. There is no code path that reads another org's documents.
- Web-cached pages (`org_id NULL`) and the public corpus are readable by all orgs; never their submissions.
- Uploaded files are private objects in MinIO; the browser gets a 10-minute presigned URL, never a public link.
- Secrets come from environment variables only (`.env`, never committed).

## Scaling path (not needed now)

| Bottleneck | Move |
|---|---|
| AI detection too slow | second Celery worker on a GPU host, queue `gpu` |
| fingerprints > ~2B rows | fingerprint store to RocksDB/ScyllaDB behind the same `index.py` interface |
| Web traffic | API to 2+ containers behind Caddy; Postgres to managed (Neon) |
