# 07 · Deployment — one VPS with Docker

Target: a single VPS (8 vCPU, 32 GB RAM, 200 GB NVMe — Hetzner CPX51 or equivalent, ~AU$90/month). Enough for Wikipedia-scale fingerprints, the API, and CPU-quantised AI models.

## Containers

```
caddy     :80 :443   TLS (auto Let's Encrypt), serves web/ static, proxies /api → api
api       :8000      uvicorn, 2 workers
worker               celery, concurrency 2 (one slow model job + one fast)
web                  build-only container producing static bundle → shared volume for caddy
postgres  :5432      volume pgdata (backed up nightly)
redis     :6379      volume redisdata
minio     :9000/9001 volume miniodata
```

## docker-compose.prod.yml (shape)

```yaml
services:
  caddy:    { image: caddy:2, ports: ["80:80","443:443"], volumes: [./infra/Caddyfile:/etc/caddy/Caddyfile, webdist:/srv, caddy_data:/data] }
  api:      { build: {context: ., dockerfile: infra/api.Dockerfile}, env_file: .env, depends_on: [postgres, redis, minio], command: uvicorn app.main:app --host 0.0.0.0 --workers 2 }
  worker:   { build: {context: ., dockerfile: infra/worker.Dockerfile}, env_file: .env, depends_on: [postgres, redis, minio], command: celery -A app.workers.celery_app worker -c 2 -Q default,gpu, volumes: [models:/models] }
  web:      { build: {context: ., dockerfile: infra/web.Dockerfile}, volumes: [webdist:/dist] }
  postgres: { image: postgres:16, env_file: .env, volumes: [pgdata:/var/lib/postgresql/data], shm_size: 1g }
  redis:    { image: redis:7, volumes: [redisdata:/data] }
  minio:    { image: minio/minio, command: server /data --console-address ":9001", env_file: .env, volumes: [miniodata:/data] }
volumes: { pgdata: {}, redisdata: {}, miniodata: {}, models: {}, webdist: {}, caddy_data: {} }
```

## Caddyfile

```
swipe.example.com {
  handle /api/* { reverse_proxy api:8000 }
  handle { root * /srv  file_server  try_files {path} /index.html }
  encode gzip
}
```

## Environment (.env)

```
DATABASE_URL=postgresql+psycopg://swipe:***@postgres:5432/swipe
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000  S3_ACCESS_KEY=…  S3_SECRET_KEY=…
JWT_SECRET=…  (openssl rand -hex 32)
BRAVE_API_KEY=…  STRIPE_SECRET_KEY=…  STRIPE_WEBHOOK_SECRET=…
SMTP_URL=…  (invitations, password reset)
```

## Operations

| Task | How |
|---|---|
| Deploy | `git pull && docker compose -f docker-compose.prod.yml up -d --build` |
| Migrate | `docker compose exec api alembic upgrade head` (run before restarting workers) |
| Backup | `infra/backup.sh` nightly via cron: `pg_dump` + `mc mirror` MinIO → off-box (Backblaze B2) |
| Logs | `docker compose logs -f api worker`; JSON logs with request_id |
| Monitoring | Uptime Kuma container + healthchecks `GET /api/health` (checks DB, Redis, MinIO) |
| Postgres tuning | `shared_buffers=8GB`, `effective_cache_size=24GB`, `work_mem=64MB`, `maintenance_work_mem=2GB` for index builds |
| Ingest corpus | `make ingest-wikipedia` (streams dump from MinIO, COPY into partitions, ~6 h) |

## Security checklist before launch

- Firewall: only 22, 80, 443 open. Postgres/Redis/MinIO not exposed.
- SSH keys only; fail2ban.
- Secrets in `.env` with `chmod 600`; never in git.
- Upload validation: extension + magic bytes + size; extraction in the worker, never the API.
- Rate limits on auth and checks; CORS locked to the app origin.
- Presigned URLs for every file download; 10-minute expiry.
- Privacy policy and terms published; data-deletion endpoint for orgs.

## Later moves

GPU worker on RunPod/Modal (same image, `-Q gpu`); managed Postgres (Neon) if the box's disk becomes the limit; second API container if traffic demands it. None require code changes.
