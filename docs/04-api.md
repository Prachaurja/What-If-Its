# 04 · API specification

Base URL `/api/v1`. JSON everywhere except uploads (multipart). Auth via `Authorization: Bearer <jwt>` or `X-API-Key`. Active org via `X-Org-Id` (defaults to the user's first org). Errors are `{ "error": { "code": "...", "message": "..." } }`.

## Auth

| Method | Path | Body / notes | Returns |
|---|---|---|---|
| POST | /auth/register | email, password, name, org_type | user + access token; creates individual org |
| POST | /auth/login | email, password | access token (15 min); refresh token in httpOnly cookie |
| POST | /auth/refresh | cookie | new access token |
| POST | /auth/logout | — | clears cookie |
| GET  | /auth/me | — | user, orgs[], active org, role |

## Organisations

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | /orgs | any | create institution/publisher org; caller becomes owner |
| GET | /orgs/{id} | member | settings, plan, usage summary |
| PATCH | /orgs/{id} | admin | name, settings |
| GET | /orgs/{id}/members | member | |
| POST | /orgs/{id}/invitations | admin | email, role → sends email with token |
| POST | /invitations/{token}/accept | signed-in | joins org |
| DELETE | /orgs/{id}/members/{user_id} | admin | |
| GET/POST/DELETE | /orgs/{id}/api-keys | admin | POST returns plaintext once |

## Checks

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | /checks | member | multipart `file` **or** JSON `{title,text}`; `options` JSON. Rate-limited, quota-checked. → `202 {id, status:"queued"}` |
| GET | /checks | viewer | list, paginated; filters: status, min_similarity, date range, created_by; sort |
| GET | /checks/{id} | viewer | `{id,status,similarity_pct,ai_prob,ai_band,payload?}` — payload only when done |
| DELETE | /checks/{id} | admin or creator | also removes the submission from the repository |
| GET | /checks/{id}/export.pdf | viewer | presigned URL to generated PDF |
| GET | /checks/{id}/sources/{doc_id} | viewer | source text + aligned passages for side-by-side view |

`options`:

```json
{ "exclude_quotes": true, "exclude_references": true,
  "run_ai": true, "web_fallback": true,
  "repositories": ["org", "public"] }
```

## Sources (reference repository)

| Method | Path | Role | Notes |
|---|---|---|---|
| GET | /sources | member | org's kind=source documents, paginated, search by title |
| POST | /sources | admin | multipart, multiple files; each queues `fingerprint_source` |
| DELETE | /sources/{id} | admin | |
| GET | /sources/stats | member | doc count, word count, last indexed |

## Usage & billing

| Method | Path | Notes |
|---|---|---|
| GET | /usage | current month vs plan limits |
| POST | /billing/checkout | Stripe Checkout session URL for a plan |
| POST | /billing/portal | Stripe customer portal URL |
| POST | /billing/webhook | Stripe → updates `organisations.plan` |

## Rate limits

| Scope | Limit |
|---|---|
| /auth/login per IP | 10 / min |
| all endpoints per user | 120 / min |
| POST /checks per org | plan quota per month + 10 / min burst |
| upload size | 10 MB; 50,000 words |

## Versioning

Path-versioned (`/v1`). Payload has `meta.engine_version` so old reports remain renderable when detectors change.
