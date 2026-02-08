# Story 2.6: Run summary metrics and zero-results logging

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want run summaries and visibility into zero-result queries,
so that I can understand run outcomes and tune inputs.

## Acceptance Criteria

1. **Given** a run completes
   **When** metrics are computed
   **Then** the system records trigger time, duration, new jobs count, and overall status
   **And** relevant count is included (0 if no labels exist yet)
2. **Given** a query returns zero results
   **When** that happens
   **Then** the system logs it with query and domain context
   **And** the log entry is linked to the run
3. **Given** a run finishes
   **When** I request the last run status
   **Then** the latest status and summary metrics are available via the API
   **And** the response includes a run identifier

## Tasks / Subtasks

- [x] Compute and persist run summary metrics (AC: 1, 3)
  - [x] Capture triggerTime and completion time; compute duration in milliseconds and overall status
  - [x] Derive newJobsCount from results created for the run; relevantCount defaults to 0 when no labels exist
  - [x] Persist metrics in SQLite with runId as the key (runs table or run_summary table)
  - [x] Emit metrics in `run.completed`/`run.failed` events for API consumption
- [x] Log zero-result queries per run (AC: 2)
  - [x] Record query text, domain, runId, and occurredAt whenever a query x domain yields zero results
  - [x] Persist zero-result logs in SQLite with a runId foreign key and index for run lookups
- [x] Expose latest run summary via API (AC: 1, 3)
  - [x] Extend `ReportsController` with a latest run summary endpoint (or `GET /api/reports/runs` latest query)
  - [x] Return runId, status, triggerTime, durationMs, newJobsCount, relevantCount in camelCase JSON
  - [x] Use RFC 7807 Problem Details for error responses
- [x] Update run summary UI (FR35 / UX) (AC: 1, 3)
  - [x] Fetch latest run summary via TanStack Query and render in the Run Summary Bar
  - [x] Include last run time, new count, relevant count, and status messaging
- [x] Add targeted tests (AC: 1-3)
  - [x] ML tests for zero-result detection and summary metric calculations
  - [x] API tests for latest run summary response shape and status handling
  - [x] Frontend tests for run summary bar rendering (if UI implemented)

## Dev Notes

### Developer Context

- This story completes Epic 2 reporting requirements (FR34-FR37) and powers the UX Run Summary Bar.
- It depends on run lifecycle tracking (Story 2.1) and result ingestion (Stories 2.3-2.4) to compute metrics and link logs.
- Zero-result logs are a tuning tool; they must capture query + domain and stay linked to the run that produced them.

### Technical Requirements

- Use runId as the stable identifier across metrics, zero-result logs, and API responses.
- triggerTime is the run start timestamp; durationMs = completedAt - triggerTime.
- newJobsCount counts new result records created for the run (exclude cached/skipped entries).
- relevantCount is derived from labeled results; default to 0 when no labels exist.
- Run status must align with event status values (success/failed/partial) and be exposed in the summary response.
- API JSON responses must be camelCase and include `runId` plus the summary metrics.

### Architecture Compliance

- ML publishes `run.*` events to Redis Streams `ml:run-events` using the standard envelope fields.
- API consumes run events and persists summary metrics to the active SQLite file.
- ML writes a new SQLite copy and swaps `data/db/current-db.txt`; do not write to the active DB after swap.
- Reports endpoints belong under `/api/reports` with controllers in `com.jobato.api.controller`.

### Library / Framework Requirements

- API: Spring Boot 3.5.10.RELEASE (Java 17) with SpringDoc 2.7.0; use ProblemDetail for RFC 7807 errors.
- ML: FastAPI + SQLAlchemy 2.0.46 + Alembic 1.18.3 for schema changes.
- Frontend: React Router 7.13.0 + TanStack Query 5.90.20; no ad-hoc caching.

### File Structure Requirements

- ML pipeline: `ml/app/pipelines/run_pipeline.py` for metrics and zero-result capture.
- ML persistence: `ml/app/db/models.py` and `ml/app/db/migrations/` for new tables/fields.
- API reports: `api/src/main/java/com/jobato/api/controller/ReportsController.java` and `api/src/main/java/com/jobato/api/service/ReportService.java`.
- API events: `api/src/main/java/com/jobato/api/messaging/RunEventsConsumer.java` (or existing consumer location).
- Frontend reports: `frontend/src/features/reports/api/reports-api.ts`, `frontend/src/features/reports/components/RunReport.tsx`, `frontend/src/features/reports/hooks/use-reports.ts`.

### Testing Requirements

- ML tests in `ml/tests/` for metric calculation, zero-result logging, and run linkage.
- API tests in `api/src/test/java` for latest summary endpoint and JSON casing.
- Frontend tests co-located for run summary bar rendering and empty/zero-result states.

### Project Structure Notes

- Keep feature ownership aligned: reports in `frontend/src/features/reports` and API report logic in `ReportService`.
- Use shared config/data volumes (`config/`, `data/`) and maintain service boundaries across frontend, API, ML.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: Run & Capture Results]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns (Redis Streams)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Run Summary Bar]
- [Source: _bmad-output/project-context.md#Critical Implementation Rules]

### Project Context Reference

- Use camelCase for API JSON fields; no snake_case in responses.
- Redis event envelope fields are required: `eventId`, `eventType`, `eventVersion`, `occurredAt`, `runId`.
- ML must never write to the active SQLite file after pointer swap.
- Use TanStack Query for server data; avoid ad-hoc caches.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- Validation workflow file not found: `_bmad/core/tasks/validate-workflow.xml`
- Previous story file not found for 2.5; previous-story intelligence skipped

### Completion Notes List

- Story drafted from epics, architecture, PRD, UX, and project-context sources.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- Sprint status updated to ready-for-dev.

### File List

- _bmad-output/implementation-artifacts/2-6-run-summary-metrics-and-zero-results-logging.md
