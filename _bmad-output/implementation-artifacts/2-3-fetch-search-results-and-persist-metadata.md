# Story 2.3: Fetch search results and persist metadata

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want the system to fetch search results for each query x allowlist pair,
so that I can review job opportunities found in the run.

## Acceptance Criteria

1. Given enabled queries and allowlisted domains, when a run executes, then the system calls Google Search for each query x domain combination, and each call is associated with the run ID.
2. Given a result URL redirects once, when the system fetches it, then it follows a single redirect and stores the final URL.
3. Given a 404 response, when the system encounters it, then the result is ignored and no record is created for that result.
4. Given valid results, when they are persisted, then job metadata (title, snippet, domain, query, timestamps) is stored and each result is linked to the run.

## Tasks / Subtasks

- [x] Task 1: Query x domain fetch loop and response mapping (AC: 1,4)
  - [x] Load enabled queries and allowlists and generate combinations (reuse Epic 1 logic if present).
  - [x] Call Google Search for each combination using runId context for logging/metrics.
  - [x] Map response items to result metadata records and persist to the run SQLite file.
- [x] Task 2: Redirect resolution and 404 handling (AC: 2,3)
  - [x] Resolve result URLs with a single redirect max and store final URL.
  - [x] If resolver returns 404, skip persistence and record skip reason (log/metric).
- [x] Task 3: Schema alignment for result metadata (AC: 4)
  - [x] Update ML SQLAlchemy models and Alembic migration with required fields.
  - [x] Ensure schema matches API Flyway expectations and naming rules (snake_case).
- [x] Task 4: Tests (AC: 1-4)
  - [x] Unit tests for google_search client call count and runId association.
  - [x] Unit tests for redirect resolver and 404 skip behavior.
  - [x] Persistence test for result records linked to runId.

## Dev Notes

### Developer Context

- Dependencies: Epic 1 stories for query/allowlist management and combinations; Epic 2.1 for run lifecycle and runId availability.
- ML ingestion is the owner for search fetching and metadata persistence. Use the existing pipeline/service boundaries.

### Technical Requirements

- Each query x allowlist pair triggers one search call and is linked to runId.
- Persist metadata fields at minimum: title, snippet, domain (displayLink), query string, timestamps, runId, raw URL, final URL.
- Follow a single redirect and store the final URL. Ignore and skip results that return 404.
- Do not implement caching, revisit throttling, or quota enforcement here (handled in Stories 2.2 and 2.5).

### Architecture Compliance

- ML writes to a new SQLite file per run, then swaps pointer; never write to the active DB after swap.
- SQLite stores post-processed metadata only. Raw/canonical HTML lives under data/html/* and is handled in Story 2.4.
- Redis Streams event envelope fields must be preserved (eventId, eventType, eventVersion, occurredAt, runId, payload).
- API JSON uses camelCase; DB tables/columns use snake_case.

### Library and Framework Requirements

- ML stack: FastAPI (Python 3), SQLAlchemy 2.0.46, Alembic 1.18.3, Redis Streams on Redis 8.4.
- Keep ML service code under ml/ only; no cross-service shared code.

### File Structure Requirements

- Primary ML modules: ml/app/pipelines/ingestion.py, ml/app/services/google_search.py, ml/app/services/fetcher.py, ml/app/db/models.py, ml/app/db/migrations/, ml/app/schemas/results.py.
- Configuration inputs live under config/ (queries/allowlists). Treat as read-only in this story.

### Testing Requirements

- ML tests live in ml/tests/ using pytest.

### Latest Tech Information

- Google Custom Search JSON API requires a Programmable Search Engine ID (cx) and API key; endpoint GET https://customsearch.googleapis.com/customsearch/v1.
- API is closed to new customers; transition deadline Jan 1, 2027. If no existing CSE access, confirm alternative search provider (e.g., Vertex AI Search) before implementation.

### Out of Scope

- Quota enforcement, caching, revisit throttling, raw HTML capture, dedupe, scoring, UI updates.

### Project Structure Notes

- Follow the top-level service boundaries (frontend/, api/, ml/, config/, data/); do not place ML logic outside ml/.
- Keep naming conventions: DB snake_case, API JSON camelCase, event names dot-lowercase.

### References

- Epic Story 2.3 requirements and AC: _bmad-output/planning-artifacts/epics.md#Story 2.3: Fetch search results and persist metadata
- Dependencies (queries/allowlists, combinations, run lifecycle): _bmad-output/planning-artifacts/epics.md#Story 1.2: Manage query strings, _bmad-output/planning-artifacts/epics.md#Story 1.3: Manage allowlist domains, _bmad-output/planning-artifacts/epics.md#Story 1.4: Generate per-site query combinations, _bmad-output/planning-artifacts/epics.md#Story 2.1: Manual run request and lifecycle tracking
- Data architecture and storage rules: _bmad-output/planning-artifacts/architecture.md#Data Architecture, _bmad-output/planning-artifacts/architecture.md#Data Boundaries
- ML ingestion ownership and file mapping: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping
- Event envelope rules: _bmad-output/planning-artifacts/architecture.md#Communication Patterns, _bmad-output/project-context.md#Critical Implementation Rules
- Naming conventions: _bmad-output/planning-artifacts/architecture.md#Naming Patterns
- Results fields to support UI: _bmad-output/planning-artifacts/prd.md#Results Review UI
- Google Custom Search JSON API docs: https://developers.google.com/custom-search/v1/overview
- Google Custom Search API method reference: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

N/A

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Confirm search API choice and credentials (CSE ID and API key) before coding.
- Company/posted-date fields may not be available from search results; confirm schema expectations.
- Implemented ML ingestion flow with query/allowlist loading, search execution per run input, URL resolution, and result metadata persistence.
- Added Google Custom Search client, URL resolver with single-redirect handling, and skip logging for 404s.
- Added SQLAlchemy run_items model plus Alembic migration and repository/session helpers.
- Added pytest coverage for search calls, redirect handling, 404 skip behavior, and persistence; tests run: `source ml/.venv/bin/activate && python -m pytest`, `./gradlew test`, `npm test`.

### File List

- _bmad-output/implementation-artifacts/2-3-fetch-search-results-and-persist-metadata.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- ml/app/pipelines/ingestion.py
- ml/app/schemas/results.py
- ml/app/services/google_search.py
- ml/app/services/fetcher.py
- ml/app/db/models.py
- ml/app/db/session.py
- ml/app/db/results_repository.py
- ml/app/db/__init__.py
- ml/app/db/alembic.ini
- ml/app/db/migrations/env.py
- ml/app/db/migrations/versions/20260208_create_run_items.py
- ml/tests/test_ingestion.py
- ml/tests/test_fetcher.py
- ml/tests/test_results_persistence.py
- ml/tests/test_google_search.py

## Change Log

- 2026-02-08: Implemented ML ingestion, URL resolution, run_items schema/migration, and tests for Story 2.3.
