# Jobato Epic 1 & 2 Guide

This guide describes how to run Jobato and perform basic Epic 1 and Epic 2 verification flows using Docker Compose and API calls.

## What Runs

The repository includes `docker-compose.yml`, which runs all core services for Epic 1:
- Frontend (Vite React)
- API (Spring Boot)
- ML (FastAPI)
- Redis

## Step-by-Step: Run Everything (Docker Compose)

1. Copy the root env file if you have not already:
```bash
cd /Users/pedro/Dev/jobato
cp .env.example .env
```

2. Start all services:
```bash
docker compose up --build
```

3. Verify endpoints:
- Frontend: http://localhost:5173
- API: http://localhost:8080/api
- ML: http://localhost:8000
- Redis: localhost:6379

4. Health checks:
```bash
curl http://localhost:8080/api/health
curl http://localhost:8000/health
```

If your environment enforces API keys, add:
```bash
-H "X-Jobato-Api-Key: <value>"
```

## Epic 2 Setup

Before validating Epic 2 flows, confirm:
- `config/quota.yaml` exists and includes `dailyLimit`, `concurrencyLimit`, and `resetPolicy`.
- At least one enabled query and allowlist domain (use the Epic 1 APIs or edit `config/queries.yaml` and `config/allowlists.yaml`).
- `data/` is writable; the API uses `data/db/runs/active.db` unless `data/db/current-db.txt` points elsewhere.
- Redis is running (Docker Compose starts it) and streams are enabled (`jobato.redis.streams.enabled` defaults to true).

## Epic 1 Basic Verification Flows

### Story 1.1: Baseline Scaffold

- The health checks above should return HTTP 200.
- Optional container check:
```bash
docker compose ps
```

### Story 1.2: Manage Query Strings

1. List queries:
```bash
curl http://localhost:8080/api/queries
```

2. Create a query:
```bash
curl -X POST http://localhost:8080/api/queries \
  -H "Content-Type: application/json" \
  -d '{"text":"senior backend remote"}'
```

3. Edit a query (replace `<id>` with the returned id):
```bash
curl -X PATCH http://localhost:8080/api/queries/<id> \
  -H "Content-Type: application/json" \
  -d '{"text":"staff backend remote"}'
```

4. Disable a query:
```bash
curl -X PATCH http://localhost:8080/api/queries/<id> \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

5. Duplicate check (should return RFC 7807 error):
```bash
curl -X POST http://localhost:8080/api/queries \
  -H "Content-Type: application/json" \
  -d '{"text":"staff backend remote"}'
```

Persisted config is written to:
- `/Users/pedro/Dev/jobato/config/queries.yaml`

### Story 1.3: Manage Allowlist Domains

1. List allowlists:
```bash
curl http://localhost:8080/api/allowlists
```

2. Add a domain:
```bash
curl -X POST http://localhost:8080/api/allowlists \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com"}'
```

3. Disable a domain:
```bash
curl -X PATCH http://localhost:8080/api/allowlists/example.com \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

4. Invalid domain (should return RFC 7807 error):
```bash
curl -X POST http://localhost:8080/api/allowlists \
  -H "Content-Type: application/json" \
  -d '{"domain":"https://bad.example.com/path"}'
```

Persisted config is written to:
- `/Users/pedro/Dev/jobato/config/allowlists.yaml`

### Story 1.4: Generate Per-Site Query Combinations

Run the unit test for the run input builder:
```bash
cd /Users/pedro/Dev/jobato/api
./gradlew test --tests "com.jobato.api.service.RunInputServiceTest"
```

There is no public HTTP endpoint for combinations; they are generated when you call `POST /api/runs` in Epic 2.

## Epic 2 Basic Verification Flows

### Story 2.1: Manual Run Request and Lifecycle Tracking

1. Trigger a run:
```bash
curl -X POST http://localhost:8080/api/runs
```

2. Fetch the run status (replace `<runId>`):
```bash
curl http://localhost:8080/api/runs/<runId>
```

3. Inspect the latest `run.requested` event in Redis:
```bash
docker compose exec redis redis-cli XREVRANGE ml:run-events + - COUNT 1
```

4. While the run is still `running`, a second trigger should be rejected:
```bash
curl -X POST http://localhost:8080/api/runs
```

Expected error code: `RUN_IN_PROGRESS`.

5. If no ML worker is publishing completion events yet, simulate one:
```bash
EVENT_ID=$(uuidgen)
OCCURRED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
docker compose exec redis redis-cli XADD ml:run-events * eventId "$EVENT_ID" eventType run.completed eventVersion 1 occurredAt "$OCCURRED_AT" runId "<runId>" payload "{\"status\":\"completed\"}"
```

6. Re-check the run status:
```bash
curl http://localhost:8080/api/runs/<runId>
```

### Story 2.2: Quota and Concurrency Enforcement

1. Review or adjust `config/quota.yaml` to match the limits you want to validate.

2. Seed the quota usage DB to simulate a quota block:
```bash
sqlite3 data/db/quota/quota.db "CREATE TABLE IF NOT EXISTS quota_usage (day TEXT, run_id TEXT, count INTEGER, PRIMARY KEY(day, run_id)); INSERT OR REPLACE INTO quota_usage (day, run_id, count) VALUES (date('now'), 'seed-run', 999);"
```

3. Trigger a run and expect `QUOTA_REACHED`:
```bash
curl -X POST http://localhost:8080/api/runs
```

4. To validate ML concurrency and quota logic (requires ML deps installed):
```bash
python -m pytest ml/tests/test_run_pipeline.py
```

### Story 2.3: Fetch Search Results and Persist Metadata

1. Ensure enabled queries and allowlist domains (Epic 1 steps above).

2. After a run completes and the ML worker processes it, inspect the run DB:
```bash
sqlite3 data/db/runs/<runId>.db "SELECT run_id, title, domain, raw_url, final_url FROM run_items LIMIT 5;"
```

3. 404 results should be skipped; look for `ingestion.skip_404` in ML logs.

### Story 2.4: Capture Raw HTML and Visible Text

1. After ingestion, confirm raw HTML files exist under:
- `/Users/pedro/Dev/jobato/data/html/raw`

2. Validate HTML capture fields on stored results:
```bash
sqlite3 data/db/runs/<runId>.db "SELECT raw_html_path, visible_text FROM run_items WHERE raw_html_path IS NOT NULL LIMIT 5;"
```

### Story 2.5: Cache Results and Revisit Throttling

1. Run the same inputs twice within 12 hours and confirm the ML worker logs cache hits (`cache.hit`).
2. Revisit the same URL within 7 days and confirm it is skipped with a revisit throttle reason.

### Story 2.6: Run Summary Metrics and Zero-Results Logging

1. Fetch the latest run summary:
```bash
curl -i http://localhost:8080/api/reports/runs/latest
```

2. Zero-result queries should be logged by the ML worker; check ML logs when a query/domain returns zero results.

## Disclaimer

This guide reflects the state of the project at the end of Epic 2 as of February 8, 2026. Subsequent epics may change commands, endpoints, or verification steps.
