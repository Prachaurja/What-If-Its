# 08 · Roadmap

Each phase ends with something demonstrable. Estimates assume part-time work alongside study.

## Phase 0 — Foundation (1 week)
- Monorepo layout from doc 02; `docker-compose.yml` with Postgres, Redis, MinIO.
- Alembic set up; schema from doc 03 as the first migration.
- Port the working v1 similarity engine into `api/app/services/similarity/`; add winnowing; partitioned `fingerprints`.
- Tests green. **Demo:** `make dev` brings up the stack; `pytest` passes.

## Phase 1 — Detector that's worth shipping (3 weeks)
- Binoculars implementation (4-bit Falcon pair on CPU).
- RAID evaluation harness; publish the first accuracy table.
- Dataset builder (human / ai / paraphrased); fine-tune DeBERTa on Colab.
- Stacker + isotonic calibration; min-length rule; confidence band.
- **Demo:** evaluation table showing ≥ 90% accuracy, ≤ 3% FPR on human essays.

## Phase 2 — Queue, auth, orgs (2 weeks)
- Celery worker; `POST /checks` returns 202; polling endpoint.
- Auth (JWT + refresh, argon2), orgs, memberships, roles, invitations, API keys.
- Rate limits and plan quotas.
- **Demo:** two orgs on one instance cannot see each other's checks; a check runs in the background.

## Phase 3 — React frontend (3 weeks)
- Screens 01–06 from doc 06; manuscript renderer as reusable components.
- Report side-by-side, AI heatmap tab, PDF export.
- **Demo:** end-to-end: sign in → upload → watch status → annotated report → export.

## Phase 4 — Coverage (2 weeks)
- Wikipedia ingestion; arXiv next.
- Web fallback with Brave API + cache.
- Quote/reference exclusion.
- **Demo:** a paragraph lifted from a random news site is caught.

## Phase 5 — Launch prep (2 weeks)
- Stripe plans; usage metering.
- Production compose, Caddy, backups, monitoring; security checklist.
- Privacy policy, terms, "how to read an AI score" page.
- Beta with 3 friendly users — one from each segment.
- **Demo:** paying customer can sign up without you touching anything.

## After launch
LMS integration (LTI 1.3 for Moodle/Canvas), Google Docs add-on, multi-language support, GPU worker, RocksDB fingerprint store, audit log, SSO (SAML) for institutions.

## Success metrics
- Detector: accuracy and FPR per doc 05, re-evaluated whenever a major model ships.
- Product: time from upload to report < 60 s at p95; zero cross-org data exposure; > 95% of checks complete without error.
- Business: 10 paying orgs within 3 months of launch, one per segment at minimum.
