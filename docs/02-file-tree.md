# 02 · Repository file tree

One repository, two apps (`api`, `web`), shared docs and infra.

```
swipe/
├── README.md
├── docker-compose.yml               # dev: postgres, redis, minio
├── docker-compose.prod.yml          # prod: + caddy, api, worker, web
├── .env.example
├── Makefile                         # make dev / test / migrate / ingest-wikipedia
│
├── docs/                            # this blueprint, kept next to the code
│   ├── 00-overview.md … 08-roadmap.md
│   └── wireframes/*.png
│
├── api/                             # Python 3.12 · FastAPI · SQLAlchemy 2 · Celery
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/            # migrations (never use create_all in prod)
│   ├── app/
│   │   ├── main.py                  # app factory, routers, middleware, error handlers
│   │   ├── core/
│   │   │   ├── config.py            # Settings from env (pydantic-settings)
│   │   │   ├── security.py          # argon2 hashing, JWT create/decode, API-key hashing
│   │   │   ├── deps.py              # get_db, current_user, current_org, require_role
│   │   │   ├── ratelimit.py         # slowapi setup, per-plan quota check
│   │   │   ├── storage.py           # S3/MinIO client, presigned URLs
│   │   │   └── logging.py           # JSON logs with request_id
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── base.py
│   │   ├── models/
│   │   │   ├── account.py           # Organisation, User, Membership, ApiKey, Invitation
│   │   │   ├── document.py          # Document, Fingerprint
│   │   │   ├── check.py             # Check, CheckSource
│   │   │   └── usage.py             # Usage
│   │   ├── schemas/                 # pydantic request/response models, one per router
│   │   ├── routers/
│   │   │   ├── auth.py              # /auth/register /login /refresh /logout /me
│   │   │   ├── orgs.py              # /orgs, /orgs/{id}/members, /invitations, /api-keys
│   │   │   ├── checks.py            # POST /checks, GET /checks, GET /checks/{id}, /export
│   │   │   ├── sources.py           # /sources CRUD + bulk upload
│   │   │   ├── usage.py             # /usage (this month, plan limits)
│   │   │   └── billing.py           # /billing/checkout, /billing/webhook (Stripe)
│   │   ├── services/                # pure logic, no HTTP
│   │   │   ├── extract.py           # docx / pdf / txt / md → text + paragraph map
│   │   │   ├── exclusions.py        # detect quotes, references section
│   │   │   ├── similarity/
│   │   │   │   ├── normalise.py
│   │   │   │   ├── shingle.py
│   │   │   │   ├── winnow.py
│   │   │   │   ├── index.py         # insert + candidate lookup (Postgres)
│   │   │   │   ├── match.py         # exact rescoring, passage merge, per-source %
│   │   │   │   └── web_fallback.py  # distinctive sentences → search → fetch → match
│   │   │   ├── ai_detect/
│   │   │   │   ├── binoculars.py
│   │   │   │   ├── deberta.py
│   │   │   │   ├── features.py      # length, TTR, burstiness
│   │   │   │   ├── stacker.py       # logistic regression + isotonic calibration
│   │   │   │   └── ensemble.py      # runs all of the above, applies min-length rule
│   │   │   ├── report.py            # assembles the JSON payload the UI renders
│   │   │   └── export_pdf.py        # report → PDF (WeasyPrint)
│   │   └── workers/
│   │       ├── celery_app.py
│   │       └── tasks.py             # run_check, fingerprint_source, ingest_chunk
│   ├── scripts/
│   │   ├── ingest/
│   │   │   ├── wikipedia.py         # stream XML dump → documents + fingerprints (COPY)
│   │   │   ├── arxiv.py
│   │   │   └── gutenberg.py
│   │   └── ml/
│   │       ├── make_dataset.py      # human / ai / paraphrased corpus builder
│   │       ├── train_deberta.py
│   │       ├── train_stacker.py
│   │       └── evaluate_raid.py     # accuracy + FPR tables per model / domain
│   └── tests/
│       ├── conftest.py              # sqlite or test-postgres fixtures
│       ├── test_similarity.py
│       ├── test_exclusions.py
│       ├── test_auth.py
│       └── test_checks_api.py
│
├── web/                             # Vite · React 18 · TypeScript · Tailwind · TanStack Query
│   ├── package.json
│   ├── vite.config.ts               # dev proxy /api → localhost:8000
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── router.tsx
│       ├── styles/tokens.css        # colour, type, spacing tokens (desk / page / ink / highlighter / redpen)
│       ├── api/
│       │   ├── client.ts            # fetch wrapper, auth header, refresh, errors
│       │   ├── auth.ts  checks.ts  sources.ts  orgs.ts  usage.ts
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useCheck.ts          # polls until status=done
│       │   └── useOrg.ts
│       ├── components/
│       │   ├── ui/                  # Button, Input, Select, Tabs, Table, Dialog, Toast, EmptyState
│       │   ├── layout/              # AppShell, Sidebar, TopBar, OrgSwitcher
│       │   ├── upload/              # Dropzone, PasteBox, CheckOptions
│       │   ├── manuscript/          # Document, Paragraph, Sentence, Highlight, SweepAnimation
│       │   └── report/              # ScoreRing, ConfidenceBand, SourceList, SourceSideBySide,
│       │                            #   AiHeatmap, ReportTabs, ExportButton
│       └── pages/
│           ├── SignIn.tsx  SignUp.tsx  AcceptInvite.tsx
│           ├── Dashboard.tsx
│           ├── NewCheck.tsx
│           ├── Report.tsx
│           ├── Sources.tsx
│           ├── Members.tsx
│           ├── Settings.tsx         # profile, org, API keys, billing
│           └── NotFound.tsx
│
└── infra/
    ├── Caddyfile
    ├── api.Dockerfile
    ├── web.Dockerfile
    ├── worker.Dockerfile            # api image + model weights layer
    └── backup.sh                    # nightly pg_dump + minio mirror → off-box
```

## Conventions

- **Routers are thin.** They validate input, check permissions, call a service, return a schema. No business logic in routers.
- **Services are pure.** They take plain Python objects and a DB session; they never import FastAPI. This is what makes them testable and reusable from Celery.
- **One model file per domain**, one schema file per router, one test file per router or service.
- **Migrations for every schema change** (`alembic revision --autogenerate -m "..."`), reviewed before commit.
- **Frontend pages compose components; components never fetch.** Fetching lives in `api/` + `hooks/`; components receive data as props.
