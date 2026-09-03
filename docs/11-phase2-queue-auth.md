# 11 · Phase 2 — job queue, auth, organisations

Phase 0/1 ran checks synchronously with no accounts. Phase 2 makes Swipe a real
multi-user service: checks run in the background, and every piece of data is
scoped to an organisation.

## What's in the code

```
api/app/core/
  security.py    bcrypt password hashing, JWT access/refresh, API-key hashing
  deps.py        current_user, current_org, require_role — the security gate
api/app/models/account.py   + ApiKey; User.is_active; Membership roles
api/app/routers/
  auth.py        /auth/register /login /refresh /logout /me
  orgs.py        /orgs members + API keys
  checks.py      now returns 202 and enqueues; list/get scoped by org
api/app/workers/
  celery_app.py  Celery on Redis
  tasks.py       run_check — the slow work, off the request path
api/tests/
  test_auth.py           register/login/token flow
  test_org_isolation.py  one org cannot see another's checks (the critical test)
  test_queue.py          enqueue -> status transitions
```

## Auth

Two ways in, one identity model:
- **Session** — email + password (bcrypt), short-lived JWT access token + a refresh
  token. The React app sends `Authorization: Bearer <token>`.
- **API key** — `X-API-Key: sk_live_...`, shown once, stored as a sha256 hash. Acts
  as the org owner. For scripts and LMS plugins.

Both resolve to `current_user`. Add `Depends(current_user)` to any route to gate it.

## Organisations

`current_org` resolves the active org (from `X-Org-Id`, the token, or the user's
first membership) and *always* verifies the user belongs to it. `require_role(...)`
gates actions by role (owner/admin/member/viewer). Every documents/checks query
filters by `org_id` — there is no path that reads another org's data, and
`test_org_isolation.py` proves it.

Sign-up auto-creates a personal organisation with the user as owner.

## The queue

`POST /checks` now:
1. stores the submission, creates a `checks` row with `status=queued`
2. calls `run_check.delay(check_id)` and returns `202 {id, status}`

The worker picks it up, flips it to `running`, does similarity + AI detection,
writes the report, sets `done` (or `failed` + error, with one retry). The frontend
polls `GET /checks/{id}` until `status=done`.

In tests, Celery runs in eager mode (synchronous, in-process) so no Redis is needed
in CI.

## Running it locally

```bash
docker compose up -d              # postgres, redis, minio
cd api
pip install -e ".[dev]"
alembic upgrade head              # applies the Phase 2 migration
# two terminals:
uvicorn app.main:app --reload
celery -A app.workers.celery_app worker --loglevel=info
```

Register, then create a check:
```bash
curl -s localhost:8000/api/v1/auth/register -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"secret123"}'      # returns access_token
curl -s localhost:8000/api/v1/checks/text -H "authorization: Bearer <token>" \
  -H 'content-type: application/json' -d '{"title":"essay","text":"..."}'   # 202 {id}
curl -s localhost:8000/api/v1/checks/<id> -H "authorization: Bearer <token>" # poll
```

## Next

Phase 3 — the React frontend (docs/06): sign-in, dashboard, the marked-up
manuscript report, sources, settings.
