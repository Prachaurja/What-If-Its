# 03 · Database schema (PostgreSQL 16)

Four groups: accounts, documents & index, checks, plumbing. Managed with Alembic.

## Accounts

```sql
CREATE TYPE org_type AS ENUM ('institution', 'publisher', 'individual');
CREATE TYPE member_role AS ENUM ('owner', 'admin', 'member', 'viewer');

CREATE TABLE organisations (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  type        org_type NOT NULL,
  plan        TEXT NOT NULL DEFAULT 'free',      -- free | pro | team | enterprise
  settings    JSONB NOT NULL DEFAULT '{}',        -- default check options, report labels
  stripe_customer_id TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  email         CITEXT UNIQUE NOT NULL,
  password_hash TEXT,                             -- NULL when SSO-only
  name          TEXT,
  is_active     BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
  user_id  INT REFERENCES users ON DELETE CASCADE,
  org_id   INT REFERENCES organisations ON DELETE CASCADE,
  role     member_role NOT NULL,
  PRIMARY KEY (user_id, org_id)
);

CREATE TABLE invitations (
  id        SERIAL PRIMARY KEY,
  org_id    INT REFERENCES organisations ON DELETE CASCADE,
  email     CITEXT NOT NULL,
  role      member_role NOT NULL,
  token     TEXT UNIQUE NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  accepted_at TIMESTAMPTZ
);

CREATE TABLE api_keys (
  id        SERIAL PRIMARY KEY,
  org_id    INT REFERENCES organisations ON DELETE CASCADE,
  key_hash  TEXT UNIQUE NOT NULL,                 -- sha256; plaintext shown once
  prefix    TEXT NOT NULL,                        -- first 8 chars, for display
  label     TEXT,
  last_used TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ
);
```

An `individual` org is created automatically at sign-up with the user as `owner`. Institutions and publishers are created explicitly and invite members.

## Documents & index

```sql
CREATE TYPE doc_kind AS ENUM ('submission', 'source', 'web');

CREATE TABLE documents (
  id          SERIAL PRIMARY KEY,
  org_id      INT REFERENCES organisations ON DELETE CASCADE,   -- NULL = shared (web cache, public corpus)
  kind        doc_kind NOT NULL,
  title       TEXT NOT NULL,
  source_url  TEXT,                               -- kind=web
  storage_key TEXT,                               -- MinIO object for the original file
  text        TEXT NOT NULL,                      -- extracted, normalised whitespace
  text_hash   CHAR(64) NOT NULL,                  -- sha256; duplicate detection
  word_count  INT NOT NULL,
  language    CHAR(2),
  indexed_at  TIMESTAMPTZ,                        -- NULL until fingerprinted
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON documents (org_id, kind, created_at DESC);
CREATE INDEX ON documents (text_hash);

-- The inverted index. No PK, partitioned, loaded with COPY.
CREATE TABLE fingerprints (
  hash    BIGINT NOT NULL,
  doc_id  INT NOT NULL,
  pos     INT NOT NULL
) PARTITION BY HASH (hash);
-- 32 partitions created by migration
CREATE INDEX ON fingerprints (hash) INCLUDE (doc_id);
```

Candidate lookup: `SELECT doc_id, count(*) FROM fingerprints WHERE hash = ANY($1) GROUP BY doc_id HAVING count(*) >= 3`. Scoping to the org's repository + shared corpus is a join to `documents` on the resulting ids.

## Checks

```sql
CREATE TYPE check_status AS ENUM ('queued', 'running', 'done', 'failed');

CREATE TABLE checks (
  id             SERIAL PRIMARY KEY,
  org_id         INT NOT NULL REFERENCES organisations ON DELETE CASCADE,
  document_id    INT NOT NULL REFERENCES documents ON DELETE CASCADE,
  created_by     INT REFERENCES users,
  status         check_status NOT NULL DEFAULT 'queued',
  options        JSONB NOT NULL,                  -- {exclude_quotes, exclude_refs, run_ai, web_fallback, repos:[...]}
  similarity_pct NUMERIC(5,1),
  ai_prob        NUMERIC(4,3),                    -- NULL when not scored
  ai_band        NUMRANGE,                        -- e.g. [0.70,0.85]
  payload        JSONB,                           -- full report for the UI
  error          TEXT,
  started_at     TIMESTAMPTZ,
  finished_at    TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON checks (org_id, created_at DESC);

CREATE TABLE check_sources (
  check_id      INT REFERENCES checks ON DELETE CASCADE,
  source_doc_id INT REFERENCES documents,
  percent       NUMERIC(5,1) NOT NULL,
  passages      JSONB NOT NULL,                   -- [{start_word,end_word,text,quoted:bool}]
  PRIMARY KEY (check_id, source_doc_id)
);
```

`payload` structure:

```json
{
  "text": "...", "paragraphs": [[0, 84], [85, 210]],
  "similarity": { "percent": 23.4, "excluded_words": 61,
                  "sources": [{"doc_id": 9, "title": "...", "url": null, "percent": 12.1}],
                  "matches": [{"doc_id": 9, "start_word": 40, "end_word": 58, "quoted": false}] },
  "ai": { "scored": true, "prob": 0.78, "band": [0.70, 0.85], "verdict": "likely",
          "sentences": [{"start_word": 0, "end_word": 22, "score": 0.91}],
          "detectors": {"binoculars": 0.72, "deberta": 0.84, "paraphrased": 0.10},
          "reason": null },
  "meta": { "word_count": 1840, "duration_ms": 8400, "engine_version": "2.1" }
}
```

## Plumbing

```sql
CREATE TABLE usage (
  org_id       INT REFERENCES organisations ON DELETE CASCADE,
  month        DATE NOT NULL,                     -- first of month
  checks_run   INT NOT NULL DEFAULT 0,
  words_checked BIGINT NOT NULL DEFAULT 0,
  web_queries  INT NOT NULL DEFAULT 0,
  PRIMARY KEY (org_id, month)
);

CREATE TABLE web_search_cache (
  query_hash  CHAR(64) PRIMARY KEY,
  urls        JSONB NOT NULL,
  fetched_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE audit_log (                          -- phase 3
  id        BIGSERIAL PRIMARY KEY,
  org_id    INT, user_id INT, action TEXT, target TEXT,
  at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Plan limits (config, not a table)

| Plan | Checks / month | Words / check | Web fallback | AI ensemble | Members |
|---|---|---|---|---|---|
| free | 10 | 5,000 | no | Binoculars only | 1 |
| pro (individual) | 200 | 30,000 | yes | yes | 1 |
| team (publisher) | 2,000 | 50,000 | yes | yes | 25 |
| enterprise (institution) | custom | 50,000 | yes | yes | unlimited |
