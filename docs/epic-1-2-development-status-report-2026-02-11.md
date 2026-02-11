# Jobato Epic 1 & 2 Development Status Report

Date: 2026-02-11

## Scope and method

- Reviewed planning artifacts and implementation artifacts for Epic 1 and Epic 2.
- Inspected implementation code across `api/`, `frontend/`, `ml/`, `config/`, and `docker-compose.yml`.
- Executed runtime checks from the guide and targeted build/test commands.

## Executive status

- Epic 1 is largely implemented and working end-to-end for core CRUD/config behaviors.
- Epic 2 is only partially implemented end-to-end.
- Biggest gap: ML is not wired to consume `run.requested` events, so Stories 2.3-2.6 are not fully operational in the live pipeline.

## Story-by-story validation

| Story | Expected | Actual | Verdict |
|---|---|---|---|
| 1.1 Set up initial project | Scaffold + compose + health + builds | Services run and health endpoints return 200; frontend/api builds pass; scaffold script passes | Implemented (with minor gaps) |
| 1.2 Manage query strings | CRUD + duplicate validation + persistence | API and UI flows work; duplicate rejected; persisted in `config/queries.yaml` | Implemented (with minor gaps) |
| 1.3 Manage allowlist domains | CRUD + validation + enable/disable | API and UI flows work; invalid domain rejected; persisted in `config/allowlists.yaml` | Implemented (with minor gaps) |
| 1.4 Generate query x domain combinations | Enabled-only combinations + run wiring + empty-input error | `run.requested` payload includes combinations and filters enabled entries | Implemented (with minor gaps) |
| 2.1 Manual run + lifecycle | Trigger + running lock + event publish + completion update | Works via API and Redis stream event flow | Implemented (with risks) |
| 2.2 Quota + concurrency | Block pre-run + enforce mid-run + partial status | Pre-run quota block works; concurrency logic exists in ML unit path | Partially implemented |
| 2.3 Fetch results + metadata | Fetch per combination + redirect + 404 skip + persistence | Ingestion code exists and unit tests exist, but not wired to live run events | Partially implemented |
| 2.4 Raw HTML + visible text | Persist raw html path + visible text + per-item error handling | Code and tests exist, but not wired to run orchestration; dependency gaps block local test collection | Partially implemented |
| 2.5 Cache + revisit throttle | 12h cache hit path + 7-day revisit skip | Service/model scaffolding exists but ingestion path does not actually use it | Not implemented end-to-end |
| 2.6 Run summary + zero-result logs | Persist run summary + latest report API + zero-result logging | Report endpoint exists but returns 204; summary persistence not wired; zero-result logging not observed | Not implemented end-to-end |

## High-impact gaps (priority)

1. **ML run orchestration missing in runtime**
   - `ml/app/main.py` only exposes `/health` and has no stream consumer for `run.requested`.
   - Result: live runs do not execute ingestion automatically.

2. **Run summary pipeline not connected**
   - `api/src/main/java/com/jobato/api/service/ReportService.java` exists, but summary persistence is not invoked from run event handling.
   - `GET /api/reports/runs/latest` returns `204` in runtime checks.

3. **Caching/revisit logic incomplete**
   - `CacheService` exists (`ml/app/services/cache.py`) and model fields exist, but ingestion does not use cache hit/miss or revisit throttle decisions.

4. **ML dependency mismatch**
   - `ml/app/services/html_fetcher.py` and `ml/app/services/html_extractor.py` require `requests` and `bs4`, but these are not listed in `ml/requirements.txt`.
   - Full local ML test collection fails due missing deps.

5. **Security/architecture drift**
   - Internal API key enforcement (`X-Jobato-Api-Key`) is not implemented on internal endpoints (and internal pointer endpoint is absent).

## Notable quality issues

- `frontend/package.json` contains duplicate devDependency keys and unpinned `vite` (`^7.2.4`).
- Root `Makefile` expected by architecture is missing.
- `api/src/test/java/com/jobato/api/JobatoApiApplicationTests.java` is still a placeholder assertion.
- Guide examples for ML tests (`python -m pytest ml/tests/test_run_pipeline.py`) fail unless `PYTHONPATH=ml` is set.

## Recommendation

- Treat Epic 1 as functionally usable.
- Treat Epic 2 as **infrastructure-complete but not product-complete** until:
  - ML consumes `run.requested` and publishes completion from real ingestion,
  - run summaries are persisted and returned by `/api/reports/runs/latest`,
  - cache/revisit logic is wired into ingestion execution,
  - ML dependency and test execution path issues are fixed.
