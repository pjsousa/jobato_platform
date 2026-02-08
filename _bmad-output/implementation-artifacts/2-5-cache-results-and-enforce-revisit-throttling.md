# Story 2.5: Cache results and enforce revisit throttling

Status: done

Story Key: 2-5-cache-results-and-enforce-revisit-throttling
Epic: 2 - Run & Capture Results

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want the system to reuse recent search results and avoid revisiting job URLs too soon,
so that runs stay efficient and within quota.

## Acceptance Criteria

1. Given cached results within the 12-hour TTL for a query x domain, when a run executes, then cached results are used instead of a new API call and the cache usage is recorded for the run.
2. Given a job URL was visited within the last week, when a run executes, then the system skips revisiting it and records the skip reason with the result.

## Tasks / Subtasks

- [x] Define cache and revisit metadata in the ML SQLite schema (AC: 1, 2)
  - [x] Add fields for cache key, cached_at, cache_expires_at, last_seen_at, and skip_reason
  - [x] Ensure schema changes use SQLAlchemy + Alembic and preserve existing data
- [x] Implement query x domain cache lookup and reuse (AC: 1)
  - [x] Read TTL from config under `config/` (add a new entry if missing)
  - [x] Short-circuit Google Search calls when cache is fresh
  - [x] Record cache hit/miss in run context and logs
- [x] Enforce 1-week revisit throttle for job URLs (AC: 2)
  - [x] Check last_seen_at/visited_at before fetching HTML
  - [x] Skip fetch within 7 days and record skip_reason = `revisit_throttle`
- [x] Add tests for cache TTL and revisit throttle (AC: 1, 2)
  - [x] Unit tests for TTL boundaries and cache hit/miss
  - [x] Unit tests for revisit throttle skip logic

## Dev Notes

### Developer Context

- This story sits inside the ingestion pipeline and directly reduces API calls and page fetches.
- Cache applies to query x domain search responses; revisit throttle applies to result URLs.
- Coordinate with run lifecycle and quota enforcement in Stories 2.1 and 2.2.

### Technical Requirements

- TTL: 12 hours; revisit throttle: 7 days.
- Cache keys should be stable (query + normalized domain) and stored in SQLite with expiry metadata.
- Cache usage must be recorded per run for observability and reporting.
- Skip reason must be persisted with the result when a URL is throttled.

### Architecture Compliance

- ML writes to a new SQLite copy, then swaps `data/db/current-db.txt`; never write to active DB after swap.
- Store raw and canonical HTML only under `data/html/*` (never in SQLite).
- Use snake_case for DB fields; keep API JSON camelCase.
- Use Redis Streams envelope only if adding new events (eventId, eventType, eventVersion, occurredAt, runId, payload).

### Library / Framework Requirements

- ML DB updates use SQLAlchemy 2.0.46 + Alembic 1.18.3.
- Prefer existing clients in `ml/app/services/google_search.py` and `ml/app/services/fetcher.py`.
- Logging is structured JSON; metrics via prometheus-client 0.24.1 if adding counters.

### File Structure Requirements

- `ml/app/pipelines/ingestion.py`
- `ml/app/services/cache.py`
- `ml/app/services/google_search.py`
- `ml/app/services/fetcher.py`
- `ml/app/db/models.py` and Alembic migrations if schema changes are needed

### Testing Requirements

- Add pytest coverage in `ml/tests/` for cache TTL and revisit throttle paths.
- Mock Google Search calls to assert no API call on cache hit.
- Cover boundary conditions (TTL expiry and 7-day cutoff).

### Project Structure Notes

- Follow ML service boundaries (`ml/app/pipelines/*`, `ml/app/services/*`, `ml/app/db/*`).
- Keep config in `config/` and `.env` per service; no cross-service shared code.

### Latest Tech Information

- Custom Search JSON API uses `https://www.googleapis.com/customsearch/v1` with `key`, `cx`, `q`.
- API limit: 100 free queries/day; paid usage costs apply. Caching reduces quota burn.
- API is closed to new customers and sunsets for existing customers by 2027-01-01. Plan for migration if needed.

### Project Context Reference

- Follow stack versions and rules in `_bmad-output/project-context.md` (naming, JSON formats, event envelope).

### References

- Epic 2 Story 2.5 acceptance criteria: `_bmad-output/planning-artifacts/epics.md`
- Caching and revisit policy: `_bmad-output/planning-artifacts/architecture.md` (Data Architecture)
- API and event patterns: `_bmad-output/planning-artifacts/architecture.md` (API & Communication Patterns)
- Project rules: `_bmad-output/project-context.md`
- Google Custom Search JSON API: https://developers.google.com/custom-search/v1/overview
- REST usage: https://developers.google.com/custom-search/v1/using_rest

## Story Completion Status

- Status set to done.
- Completion note: Cache and revisit throttling implementation completed successfully.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

None.

### Completion Notes List

- Story context compiled from epics, PRD, architecture, UX, and web research.
- No prior story file available for Epic 2.4.

### File List

- `ml/app/pipelines/ingestion.py`
- `ml/app/services/cache.py`
- `ml/app/services/google_search.py`
- `ml/app/services/fetcher.py`
- `ml/app/db/models.py`
- `ml/app/db/migrations/*`

