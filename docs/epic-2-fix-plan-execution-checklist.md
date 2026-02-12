# Epic 2 Fix Plan - Execution Checklist

Date: 2026-02-11
Mode: Story-by-story, gated

## How to use this checklist

- Complete one story at a time.
- Do not start next story until the current gate is fully checked.
- Capture command output evidence for each gate.
- Keep one branch/PR per story.

---

## Global setup (once)

- [ ] Confirm mock-provider hard gate approach is accepted.
- [ ] Confirm optional real-provider smoke test is out of hard-gate scope.
- [ ] Start fresh stack:

```bash
docker compose up -d --build
```

- [ ] API health is up:

```bash
curl -i http://localhost:8080/api/health
```

- [ ] ML health is up:

```bash
curl -i http://localhost:8000/health
```

- [ ] Pre-gate ML test path works:

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_run_pipeline.py
```

---

## Story 2.3 - Fetch search results and persist metadata

### Implementation checklist

- [ ] Add ML consumer for `run.requested` from `ml:run-events`.
- [ ] Validate event envelope fields before processing.
- [ ] Execute ingestion from `payload.runInputs`.
- [ ] Publish terminal event (`run.completed` / `run.failed`) from ML runtime.
- [ ] Replace bespoke YAML parser with YAML loader.
- [ ] Persist required metadata fields (`search_query`, ideally `query_id`).
- [ ] Remove runtime `create_all` reliance and enforce migrations.
- [ ] Harden search/fetch timeout/network error handling.
- [ ] Add/adjust tests for ingestion/event path.

### Gate 2.3 commands

```bash
RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
echo "$RUN_ID"

for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:8080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  echo "$STATUS"
  [ "$STATUS" != "running" ] && break
  sleep 2
done

sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE run_id='${RUN_ID}';"
docker compose exec redis redis-cli XREVRANGE ml:run-events + - COUNT 20
PYTHONPATH=ml python3 -m pytest ml/tests/test_ingestion.py ml/tests/test_fetcher.py ml/tests/test_results_persistence.py ml/tests/test_google_search.py
```

### Gate 2.3 pass checks

- [ ] Run reaches terminal state without manual Redis event simulation.
- [ ] `run_items` exists and has rows for the run.
- [ ] Redis stream contains matching request + completion/failure event.
- [ ] Target ML tests pass.

---

## Story 2.4 - Capture raw HTML and visible text

### Implementation checklist

- [ ] Persist HTML files under deterministic path in `data/html/raw/`.
- [ ] Persist `raw_html_path` on each result.
- [ ] Extract and persist `visible_text`.
- [ ] Persist `fetch_error` / `extract_error` without aborting run.
- [ ] Ensure UTF-8 and malformed HTML resilience.
- [ ] Align migration, model, and runtime schema.
- [ ] Add/adjust HTML service + ingestion integration tests.

### Gate 2.4 commands

Note: this gate creates a temporary unique query to avoid false failures when revisit throttling skips previously seen URLs.

```bash
GATE_QUERY="gate-2-4-html-$(date +%s)-$RANDOM"
QUERY_JSON=$(curl -s -X POST http://localhost:8080/api/queries \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"${GATE_QUERY}\"}")
QUERY_ID=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["id"])' "$QUERY_JSON")

RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')

for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:8080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
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
curl -s -X PATCH "http://localhost:8080/api/queries/${QUERY_ID}" \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}' >/dev/null
```

### Gate 2.4 pass checks

- [ ] Temporary gate query is created successfully.
- [ ] At least one row for the gate query is not throttled (`skip_reason IS NULL`).
- [ ] At least one row for the gate query has `raw_html_path`.
- [ ] At least one row for the gate query has non-empty `visible_text`.
- [ ] Referenced HTML file exists on disk.
- [ ] HTML tests pass.
- [ ] Temporary gate query is disabled during cleanup.

---

## Story 2.5 - Cache results and revisit throttling

### Implementation checklist

- [ ] Integrate cache lookup before external search call.
- [ ] Persist and enforce cache TTL metadata (`cache_key`, `cached_at`, `cache_expires_at`).
- [ ] Implement revisit throttle before fetch and set `skip_reason='revisit_throttle'`.
- [ ] Record cache hit/miss and throttle behavior in logs/metrics.
- [ ] Add/adjust tests for TTL boundary and 7-day cutoff.

### Gate 2.5 commands

```bash
# Run A
RUN_A=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:8080/api/runs/$RUN_A" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

# Run B (same inputs, within TTL)
RUN_B=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:8080/api/runs/$RUN_B" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

docker compose logs ml --tail 400 | python3 -c "import sys; t=sys.stdin.read(); print('cache.hit' in t)"
sqlite3 "data/db/runs/${RUN_B}.db" "SELECT COUNT(*) FROM run_items WHERE cache_key IS NOT NULL;"
sqlite3 "data/db/runs/${RUN_B}.db" "SELECT COUNT(*) FROM run_items WHERE skip_reason='revisit_throttle';"
PYTHONPATH=ml python3 -m pytest ml/tests/test_cache*.py
```

### Gate 2.5 pass checks

- [ ] Cache hit behavior is observable in logs/metrics.
- [ ] Cache metadata is persisted.
- [ ] Revisit throttle behavior is observable (when repeated URLs exist).
- [ ] Cache/revisit tests pass.

---

## Story 2.6 - Run summary metrics and zero-results logging

### Implementation checklist

- [ ] Wire summary persistence from run event consumer to report service.
- [ ] Persist `runId`, `status`, `triggerTime`, `durationMs`, `newJobsCount`, `relevantCount`.
- [ ] Persist zero-result logs linked to `runId` (query + domain context).
- [ ] Ensure `GET /api/reports/runs/latest` returns populated payload when available.
- [ ] Replace frontend run summary placeholders with real API data.
- [ ] Add/adjust API, ML, and frontend tests for summary and zero-result behavior.

### Gate 2.6 commands

```bash
RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:8080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

curl -i http://localhost:8080/api/reports/runs/latest
sqlite3 data/db/runs/active.db "SELECT run_id,status,duration_ms,new_jobs_count,relevant_count FROM run_summaries ORDER BY trigger_time DESC LIMIT 1;"
```

### Gate 2.6 pass checks

- [ ] Reports endpoint returns HTTP 200.
- [ ] Response contains `runId`, `status`, `triggerTime`, `durationMs`, `newJobsCount`, `relevantCount`.
- [ ] `run_summaries` table contains latest row.
- [ ] Zero-result logs exist and are linked to runId.
- [ ] UI summary bar displays real values (not placeholders).

---

## Optional smoke test (real provider)

- [ ] Configure valid real search provider credentials.
- [ ] Run one end-to-end job run.
- [ ] Confirm no regressions vs mock-gated behavior.

---

## Evidence log template (copy for each story)

```md
### Story X.Y Evidence
- Branch/PR:
- Commit SHA:
- Gate commands run:
- Gate outputs saved at:
- Pass/Fail:
- Notes:
```
