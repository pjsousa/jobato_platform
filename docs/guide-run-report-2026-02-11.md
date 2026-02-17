# GUIDE.md Run Report

Date: 2026-02-11
Source: `GUIDE.md`

## Execution context

- Docker daemon and compose available.
- Existing containers were already up (`api`, `ml`, `frontend`, `redis`) and healthy before validation.
- Validation was executed against the current running stack.

## Result summary

- Epic 1 guide steps: mostly pass.
- Epic 2 guide steps: partial pass; runtime gaps in ML orchestration and reporting block full completion.

## Detailed run-through

### Step 1 - Run everything / health checks

Status: ✅ Pass

- `docker compose ps` showed all four services up.
- `curl http://localhost:18080/api/health` returned HTTP 200 (`{"status":"UP"}`).
- `curl http://localhost:18000/health` returned HTTP 200 (`{"status":"ok","redis":"ok"}`).

### Story 1.2 - Manage query strings

Status: ✅ Pass

- `GET /api/queries` returned HTTP 200 and existing query list.
- `POST /api/queries` with `guide test query 2026-02-11` returned HTTP 201.
- `PATCH /api/queries/{id}` text update returned HTTP 200.
- `PATCH /api/queries/{id}` disable returned HTTP 200.
- Duplicate `POST /api/queries` returned HTTP 400 with RFC-style problem response and duplicate detail.

### Story 1.3 - Manage allowlist domains

Status: ✅ Pass

- `GET /api/allowlists` returned HTTP 200.
- `POST /api/allowlists` with `guide-test-jobato.com` returned HTTP 201.
- `PATCH /api/allowlists/guide-test-jobato.com` disable returned HTTP 200.
- Invalid domain `POST` (`https://bad.example.com/path`) returned HTTP 400 with clear validation detail.

### Story 1.4 - Generate per-site query combinations

Status: ✅ Pass (as validated via API test and emitted event payload)

- Ran `./gradlew test --tests "com.jobato.api.service.RunInputServiceTest"` in `api/` -> `BUILD SUCCESSFUL`.
- Triggered run and inspected Redis event:
  - `XREVRANGE ml:run-events + - COUNT 1`
  - Event type `run.requested` included `runInputs[]` with `queryId`, `queryText`, `domain`, `searchQuery`.

### Story 2.1 - Manual run request and lifecycle tracking

Status: ✅ Pass

- `POST /api/runs` created running run (HTTP 201).
- `GET /api/runs/{runId}` returned running state (HTTP 200).
- Redis stream included latest `run.requested` event with envelope fields.
- Second `POST /api/runs` while running returned HTTP 409 with `errorCode: RUN_IN_PROGRESS`.
- Simulated completion event via Redis `XADD` updated run to `completed` and set `endedAt`.

### Story 2.2 - Quota and concurrency enforcement

Status: ⚠️ Partial pass

- Seeded `data/db/quota/quota.db` with high usage (`count=999` for today).
- `POST /api/runs` returned HTTP 429 with `errorCode: QUOTA_REACHED`.
- Guide command `python3 -m pytest ml/tests/test_run_pipeline.py` failed on host (`ModuleNotFoundError: app`).
- With `PYTHONPATH=ml`, the test passes (`3 passed`).

### Story 2.3 - Fetch search results and persist metadata

Status: ❌ Fail in end-to-end guide flow

- Triggered a run and checked expected run DB:
  - `sqlite3 data/db/runs/<runId>.db "SELECT ... FROM run_items ..."`
  - Result: `no such table: run_items`
- ML service logs show health checks only; no evidence of `run.requested` consumption/ingestion processing.

### Story 2.4 - Capture raw HTML and visible text

Status: ⚠️ Partial

- `data/html/raw` contains HTML files.
- Sample historical DB (`data/db/runs/test-run-20260210-010726.db`) contains `raw_html_path` and `visible_text` rows.
- But this behavior was not produced by the current guide-triggered run (because runtime ingestion is not wired).

### Story 2.5 - Cache results and revisit throttling

Status: ❌ Fail in guide verification

- Could not validate `cache.hit` or revisit throttle behavior in live run path.
- ML logs contained no `cache.hit`, `ingestion.skip_404`, or revisit-throttle log signals during guide execution.

### Story 2.6 - Run summary metrics and zero-results logging

Status: ❌ Fail in guide verification

- `GET /api/reports/runs/latest` returned HTTP 204 (no latest summary payload).
- No zero-result logging evidence found during this run-through.

## Additional checks executed

- `python3 scripts/test_scaffold.py` -> all 7 tests passed.
- `npm run build` and `npm test` in `frontend/` passed (with duplicate-key warnings in `package.json`).
- `./gradlew build` and `./gradlew test` in `api/` passed.
- Full ML test run with `PYTHONPATH=ml` failed collection due missing deps (`requests`) used by HTML services.

## Side effects introduced by guide run

- Added/updated entries in:
  - `config/queries.yaml` (guide test query created and then disabled)
  - `config/allowlists.yaml` (`guide-test-jobato.com` created and disabled)
- Added run records in `data/db/runs/active.db`.
- Created/updated quota usage row during quota test (seed row removed after validation).

## Conclusion

- GUIDE.md currently validates Epic 1 and core Epic 2.1/2.2 API behavior.
- GUIDE.md does **not** pass end-to-end for Epic 2.3-2.6 on this runtime due missing ML event-driven orchestration and reporting wiring.
