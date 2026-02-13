# Jobato Epic 1, 2, and Epic 3 Rollout Guide

This guide describes how to run Jobato and perform basic Epic 1 and Epic 2 verification flows, plus the upcoming Epic 3 rollout checks, using Docker Compose and API calls.

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

## Epic 3 Rollout Guide (What We Will Start Doing Very Soon)

Epic 3 is being delivered story-by-story. Use the steps below to validate each new capability as soon as it lands.
Until a given story is merged, that step may return `404` or missing-field responses.

### Step 0: Pre-Gate (confirm baseline before Epic 3 checks)

1. Start services and verify health:
```bash
docker compose up -d --build
curl -i http://localhost:8080/api/health
curl -i http://localhost:8000/health
curl -i http://localhost:8080/api/reports/runs/latest
PYTHONPATH=ml python3 -m pytest ml/tests/test_ingestion.py
```

### Step 1: URL normalization for stable dedupe keys (Story 3.1)

1. Run normalization-focused tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_url_normalization.py ml/tests/test_ingestion.py
```
2. Trigger a run and wait for completion:
```bash
RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:8080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 0
done
```
3. Confirm normalized URLs are persisted:
```bash
sqlite3 "data/db/runs/${RUN_ID}.db" "PRAGMA table_info(run_items);"
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE normalized_url IS NOT NULL;"
```

### Step 2: Duplicate detection and canonical linking (Story 3.2)

1. Run dedupe tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_dedupe.py ml/tests/test_ingestion_dedupe.py
./api/gradlew test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"
```
2. Trigger a run and wait for completion (reuse Step 1 run loop if preferred).
3. Confirm duplicate linkage fields are being populated:
```bash
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE is_duplicate = 1;"
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE canonical_id IS NOT NULL;"
```

### Step 3: Baseline relevance scoring (Story 3.3)

1. Run scoring tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_scoring.py ml/tests/test_ingestion_scoring.py
./api/gradlew test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"
```
2. Trigger a run and wait for completion (reuse Step 1 run loop if preferred).
3. Verify score persistence and range:
```bash
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT MIN(relevance_score), MAX(relevance_score), COUNT(*) FROM run_items WHERE relevance_score IS NOT NULL;"
```

### Step 4: Pluggable model registry discovery (Story 3.4)

1. Run model interface/registry tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_model_interface.py ml/tests/test_registry.py
```
2. Verify ML model discovery endpoints:
```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ml/models
```

### Step 5: Parallel candidate evaluation (Story 3.5)

1. Run evaluation pipeline tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_evaluation_worker.py ml/tests/test_metrics.py ml/tests/test_evaluation_pipeline.py
```
2. Trigger evaluation and inspect status/results:
```bash
curl -i -X POST http://localhost:8080/api/ml/evaluations
curl -i http://localhost:8080/api/ml/evaluations/<evaluationId>
curl -i http://localhost:8080/api/ml/evaluations/<evaluationId>/results
```

### Step 6: Model comparison, activation, and rollback path (Story 3.6)

1. Run activation/comparison tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_model_activation.py ml/tests/test_model_selector.py
./api/gradlew test --tests "com.jobato.api.controller.MlModelControllerTest" --tests "com.jobato.api.service.MlModelClientTest"
```
2. Compare candidates and activate a model:
```bash
curl -i http://localhost:8080/api/ml/models/comparisons
curl -i -X POST http://localhost:8080/api/ml/models/<modelId>/activate
curl -i http://localhost:8080/api/ml/models/active
```

### Step 7: Daily retrain and manual retrain operations (Story 3.7)

1. Run retrain tests:
```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_retrain_scheduler.py ml/tests/test_retrain_pipeline.py ml/tests/test_retrain_no_labels.py
./api/gradlew test --tests "com.jobato.api.controller.RetrainControllerTest"
```
2. Trigger retrain and inspect status/history:
```bash
curl -i -X POST http://localhost:8080/api/ml/retrain/trigger
curl -i http://localhost:8080/api/ml/retrain/status
curl -i http://localhost:8080/api/ml/retrain/history
```

## Disclaimer

This guide reflects the state of the project through Epic 2 and the planned Epic 3 rollout checks as of February 13, 2026. As Epic 3 stories are merged, commands and endpoint contracts may be refined.
