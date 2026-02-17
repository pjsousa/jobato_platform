# Epic 2 Prioritized Fix Plan (Story-by-Story with Gates)

Date: 2026-02-11

## Decision locked

- Hard gates run with deterministic mock search provider.
- Real Google provider remains an optional smoke test only.

## Operating rules

1. Implement one story at a time.
2. Do not start the next story until the current gate passes.
3. Keep each story in a separate branch/PR with its own gate evidence.

---

## Pre-Gate (baseline before Story 2.3)

### Objective

Stabilize runtime and test execution so later gates are meaningful.

### Tasks

- Add missing ML dependencies required by current code (`requests`, `beautifulsoup4`, `pyyaml`).
- Standardize ML import path for tests (`app.*` imports).
- Fix Alembic revision chain consistency in `ml/app/db/migrations/versions/`.
- Confirm no seeded quota rows are blocking runs.

### Pre-Gate commands

```bash
docker compose up -d --build
curl -i http://localhost:18080/api/health
curl -i http://localhost:18000/health
PYTHONPATH=ml python3 -m pytest ml/tests/test_run_pipeline.py
```

### Pass criteria

- API and ML health endpoints return HTTP 200.
- ML run pipeline tests pass.

---

## Story 2.3 - Fetch search results and persist metadata

### Objective

Make run orchestration execute ingestion end-to-end and persist result metadata per run.

### Implementation tasks

- Wire ML Redis stream consumer for `run.requested`.
- Validate event envelope (`eventId`, `eventType`, `eventVersion`, `occurredAt`, `runId`, `payload`).
- Execute ingestion from `payload.runInputs`.
- Emit `run.completed` or `run.failed` from ML runtime (no manual simulation for gate).
- Replace bespoke YAML parser in ingestion with YAML loader.
- Persist missing metadata needed by story/review (`query_id` and `search_query`, or minimum `search_query`).
- Remove runtime `create_all` reliance and enforce migrations.
- Harden network/timeout error handling and map to `run.failed`.

### Gate 2.3 commands

```bash
docker compose up -d --build
RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
echo "$RUN_ID"

for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  echo "$STATUS"
  [ "$STATUS" != "running" ] && break
  sleep 2
done

sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE run_id='${RUN_ID}';"
docker compose exec redis redis-cli XREVRANGE ml:run-events + - COUNT 20
PYTHONPATH=ml python3 -m pytest ml/tests/test_ingestion.py ml/tests/test_fetcher.py ml/tests/test_results_persistence.py ml/tests/test_google_search.py
```

### Pass criteria

- Run transitions from `running` to terminal state without manual `XADD`.
- `run_items` exists in run DB and count is greater than 0 (for non-empty enabled inputs).
- Stream shows matching `run.requested` and ML `run.completed`/`run.failed`.
- Story tests pass.

---

## Story 2.4 - Capture raw HTML and visible text

### Objective

Capture raw HTML and visible text per result, with resilient per-item error handling.

### Implementation tasks

- Store HTML under deterministic path in `data/html/raw/`.
- Persist `raw_html_path`, `visible_text`, `fetch_error`, and `extract_error`.
- Ensure fetch/extract failures do not abort run.
- Ensure UTF-8 and malformed HTML resilience.
- Align migration/model/runtime schema.

### Gate 2.4 commands

Note: this gate creates a temporary unique query to prevent revisit-throttle carryover from masking HTML/text capture behavior.

```bash
GATE_QUERY="gate-2-4-html-$(date +%s)-$RANDOM"
QUERY_JSON=$(curl -s -X POST http://localhost:18080/api/queries \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"${GATE_QUERY}\"}")
QUERY_ID=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["id"])' "$QUERY_JSON")

RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')

for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE query_text='${GATE_QUERY}' AND skip_reason IS NULL;"
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE query_text='${GATE_QUERY}' AND raw_html_path IS NOT NULL;"
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE query_text='${GATE_QUERY}' AND visible_text IS NOT NULL AND length(visible_text) > 0;"

HTML_PATH=$(sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT raw_html_path FROM run_items WHERE query_text='${GATE_QUERY}' AND raw_html_path IS NOT NULL LIMIT 1;")
test -f "$HTML_PATH" && echo "OK"

PYTHONPATH=ml python3 -m pytest ml/tests/test_html_services.py ml/tests/test_ingestion_html_integration.py

# cleanup: disable temporary gate query
curl -s -X PATCH "http://localhost:18080/api/queries/${QUERY_ID}" \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}' >/dev/null
```

### Pass criteria

- Temporary gate query is created successfully.
- At least one row for that gate query is not throttled (`skip_reason IS NULL`).
- At least one persisted row for that gate query has `raw_html_path` and `visible_text`.
- Referenced HTML file exists on disk.
- HTML tests pass.
- Temporary gate query is disabled during cleanup.

---

## Story 2.5 - Cache results and revisit throttling

### Objective

Actually enforce 12-hour cache reuse and 7-day revisit throttle in live ingestion flow.

### Implementation tasks

- Integrate cache lookup before search call in ingestion loop.
- Persist and respect `cache_key`, `cached_at`, `cache_expires_at`.
- Implement revisit throttle before page fetch and set `skip_reason='revisit_throttle'`.
- Record cache hit/miss and throttle skips in logs/metrics.
- Add tests for TTL boundary and 7-day cutoff.

### Gate 2.5 commands

```bash
# Run A
RUN_A=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')

# wait A terminal
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_A" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

# Run B (same inputs, within TTL)
RUN_B=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')

# wait B terminal
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_B" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

docker compose logs ml --tail 400 | python3 -c "import sys; t=sys.stdin.read(); print('cache.hit' in t)"
sqlite3 "data/db/runs/${RUN_B}.db" "SELECT COUNT(*) FROM run_items WHERE cache_key IS NOT NULL;"
sqlite3 "data/db/runs/${RUN_B}.db" "SELECT COUNT(*) FROM run_items WHERE skip_reason='revisit_throttle';"
PYTHONPATH=ml python3 -m pytest ml/tests/test_cache*.py
```

### Pass criteria

- Run B demonstrates cache reuse (`cache.hit` log or equivalent metric evidence).
- Cache metadata is persisted.
- Revisit throttle is observable when repeat URLs are present.
- Cache/throttle tests pass.

---

## Story 2.6 - Run summary metrics and zero-results logging

### Objective

Provide complete latest-run reporting and zero-result observability.

### Implementation tasks

- Wire run summary persistence from API event consumer to `ReportService`.
- Persist `triggerTime`, `durationMs`, `newJobsCount`, `relevantCount`, `status`, `runId`.
- Persist zero-result logs linked to runId with query/domain context.
- Return populated payload on `GET /api/reports/runs/latest`.
- Replace frontend run summary placeholders with real report data.
- Add API/ML/frontend tests for summary + zero-result behavior.

### Gate 2.6 commands

```bash
RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')

for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

curl -i http://localhost:18080/api/reports/runs/latest
sqlite3 data/db/runs/active.db "SELECT run_id,status,duration_ms,new_jobs_count,relevant_count FROM run_summaries ORDER BY trigger_time DESC LIMIT 1;"
```

### Pass criteria

- `/api/reports/runs/latest` returns HTTP 200 with expected fields:
  - `runId`, `status`, `triggerTime`, `durationMs`, `newJobsCount`, `relevantCount`.
- Latest run summary row exists in SQLite.
- Zero-result logs are persisted and linked to runId.
- UI summary bar shows real values (not placeholders).

---

## Suggested delivery sequence

1. PR/Branch A: Story 2.3 only + Gate 2.3 evidence.
2. PR/Branch B: Story 2.4 only + Gate 2.4 evidence.
3. PR/Branch C: Story 2.5 only + Gate 2.5 evidence.
4. PR/Branch D: Story 2.6 only + Final gate evidence.
