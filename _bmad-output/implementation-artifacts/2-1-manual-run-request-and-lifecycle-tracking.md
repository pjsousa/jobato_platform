# Story 2.1: Manual run request and lifecycle tracking

Status: ready-for-dev
Story Key: 2-1-manual-run-request-and-lifecycle-tracking
Epic: 2 - Run and Capture Results

## Story

As a user,
I want to trigger a run and see its lifecycle state,
so that I know when a run starts, finishes, or fails.

## Acceptance Criteria

1. Given no run is in progress, when I trigger a run, then a run record is created with status "running" and the start timestamp is recorded.
2. Given a run is triggered, when the system accepts it, then a run.requested event is published to Redis Streams and the event includes runId and event metadata.
3. Given a run is already in progress, when I trigger another run, then the system rejects it with a clear "run in progress" error and no new run record is created.
4. Given ML publishes a run completion or failure event, when the API consumes the event, then the run status is updated accordingly and the end timestamp is recorded.

## Tasks / Subtasks

- [ ] Task 1: Implement run trigger endpoint (AC: 1, 2, 3)
  - [ ] Add POST /api/runs that checks for an active running run and returns RFC 7807 error when blocked
  - [ ] Create run record with status "running" and start timestamp in active SQLite DB
  - [ ] Publish run.requested event to Redis stream ml:run-events with required envelope
- [ ] Task 2: Implement run status updates from ML events (AC: 4)
  - [ ] Add consumer for run.completed and run.failed events with idempotent handling
  - [ ] Update run status and end timestamp in active SQLite DB
- [ ] Task 3: Expose run status for UI
  - [ ] Implement GET /api/runs/{id} and response DTOs in camelCase
  - [ ] Add run summary/report endpoint if needed for run summary bar
- [ ] Task 4: Wire UI run controls and status display
  - [ ] Add or extend RunControls and RunStatus UI under frontend/src/features/runs
  - [ ] Show run summary bar (last run time, new count, relevant count, quota remaining)
  - [ ] Surface run status or quota warnings in detail footer area
- [ ] Task 5: Tests and observability
  - [ ] Add API tests for run trigger, run-in-progress error, and event consumption
  - [ ] Add ML tests for event publishing format
  - [ ] Add frontend tests for run status and error states

## Dev Notes

### Developer Context

- Epic 2 focuses on reliable run orchestration and lifecycle visibility across API, ML, and UI. [Source: _bmad-output/planning-artifacts/epics.md#Epic 2]
- Manual run trigger and lifecycle visibility are MVP-critical and must surface clear status and error states. [Source: _bmad-output/planning-artifacts/prd.md#Run Orchestration]
- Lifecycle flow: UI triggers run -> API creates run + publishes run.requested -> ML processes -> ML publishes run.completed/run.failed -> API consumes and updates run record -> UI reads status. [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points]
- Desktop-first UX requires run summary visibility without breaking flow (summary bar + detail footer). [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Run Summary Bar]

### Technical Requirements

- POST /api/runs must reject overlapping runs and return RFC 7807 Problem Details with a clear "run in progress" message. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1, _bmad-output/planning-artifacts/architecture.md#API Response Formats]
- Create run record with status "running" and start timestamp in the active SQLite DB (API writes only). [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1, _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- Publish run.requested to Redis Streams stream ml:run-events using the standard envelope (eventId, eventType, eventVersion, occurredAt, runId, payload) and dot-lowercase eventType. [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns, _bmad-output/project-context.md#Critical Implementation Rules]
- API must consume run.completed and run.failed events and update run status + end timestamp; consumer must be idempotent (at-least-once delivery). [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1, _bmad-output/planning-artifacts/architecture.md#Event System Patterns]
- UI should surface last run status (success/failed/partial), run summary metrics (trigger time, duration, new jobs count, relevant count), and quota errors. [Source: _bmad-output/planning-artifacts/prd.md#Run Reporting and Status, _bmad-output/planning-artifacts/ux-design-specification.md#Run Summary Bar]
- No real-time updates in MVP; use polling via TanStack Query for status refresh. [Source: _bmad-output/planning-artifacts/prd.md#Implementation Considerations]
- Structured JSON logs for API/ML; ensure /api/health and /api/metrics are exposed. [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure and Deployment]

### Architecture Compliance

- REST + JSON under /api with plural resource paths; query params camelCase; RFC 7807 errors. [Source: _bmad-output/planning-artifacts/architecture.md#API and Communication Patterns]
- Redis Streams on Redis 8.4; stream name ml:run-events; event types run.requested/run.completed/run.failed. [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns]
- API writes to active SQLite only; ML writes to new DB, swaps pointer, then stops writing to active DB. [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture, _bmad-output/project-context.md#Critical Implementation Rules]
- Do not store raw/canonical HTML in SQLite; keep under data/html/*. [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- HTTPS for browser -> API; ML -> API uses X-Jobato-Api-Key for internal endpoints. [Source: _bmad-output/planning-artifacts/architecture.md#Authentication and Security]

### Library/Framework Requirements

- API: Spring Boot 3.5.10.RELEASE (Java 17), SpringDoc 2.7.0, Flyway 12.0.0, Micrometer 1.16.2. [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions, _bmad-output/project-context.md#Technology Stack]
- Messaging: Redis Streams on Redis 8.4.x. [Source: _bmad-output/planning-artifacts/architecture.md#API and Communication Patterns]
- Frontend: React Router 7.13.0, TanStack Query 5.90.20, react-window 2.2.6. [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions]
- ML: FastAPI with SQLAlchemy 2.0.46 + Alembic 1.18.3 for SQLite runs DB. [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]

### File Structure Requirements

- Frontend run controls/status live under frontend/src/features/runs (RunControls, RunStatus, hooks/use-runs). [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]
- API run orchestration lives in com.jobato.api.controller.RunController, service.RunService, messaging.RunEventsConsumer, repository.RunRepository. [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]
- ML run pipeline lives in ml/app/pipelines/run_pipeline.py and event schemas in ml/app/schemas/events.py. [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]
- Config files are external under config/ (quota.yaml, queries.yaml, allowlists.yaml). [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]

### Testing Requirements

- API tests in api/src/test/java: run trigger success, run-in-progress error, event consumption updates status and end timestamp. [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]
- ML tests in ml/tests: event publishing envelope fields and eventType values. [Source: _bmad-output/project-context.md#Testing Rules]
- Frontend tests co-located in frontend/src/features/runs: run status display, summary bar, and quota/run-in-progress warnings. [Source: _bmad-output/project-context.md#Testing Rules]

### Latest Tech Information

- Spring Boot latest GA is 4.0.2; 4.1.0-M1 is pre-release. Project pins 3.5.10 for Java 17 compatibility, so do not upgrade to 4.x without JDK/compat review. [Source: https://github.com/spring-projects/spring-boot/releases]
- Redis latest 8.4.1 includes security fixes; prefer 8.4.1 while staying on 8.4 line. RC 8.6 is pre-release. [Source: https://github.com/redis/redis/releases]
- React Router latest 7.13.0 matches pinned version. [Source: https://github.com/remix-run/react-router/releases]
- FastAPI latest 0.128.4; if pinning ML deps, target 0.128.4 and ensure Pydantic v2 compatibility. [Source: https://github.com/fastapi/fastapi/releases]
- TanStack Query latest patch releases are in the 5.9x line; keep 5.90.20 unless upgrading with review. [Source: https://github.com/TanStack/query/releases]

### Project Context Reference

- Enforce camelCase in API JSON and dot-lowercase event types; no snake_case in API responses. [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- Use TanStack Query for server state; no ad-hoc caches in the frontend. [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- Internal endpoints must require X-Jobato-Api-Key; never bypass. [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- ML must never write to active DB after pointer swap; API is the only writer. [Source: _bmad-output/project-context.md#Critical Implementation Rules]

### Story Completion Status

- Status set to ready-for-dev.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

### References

- _bmad-output/planning-artifacts/epics.md#Story 2.1
- _bmad-output/planning-artifacts/prd.md#Run Orchestration
- _bmad-output/planning-artifacts/architecture.md#Event System Patterns
- _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries
- _bmad-output/planning-artifacts/ux-design-specification.md#Run Summary Bar
- _bmad-output/project-context.md#Critical Implementation Rules
- https://github.com/spring-projects/spring-boot/releases
- https://github.com/redis/redis/releases
- https://github.com/remix-run/react-router/releases
- https://github.com/fastapi/fastapi/releases
- https://github.com/TanStack/query/releases

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- None

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List

- _bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
