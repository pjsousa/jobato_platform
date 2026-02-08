# Story 2.1: Manual run request and lifecycle tracking

Status: in-progress
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

- [x] Task 1: Implement run trigger endpoint (AC: 1, 2, 3)
  - [x] Add POST /api/runs that checks for an active running run and returns RFC 7807 error when blocked
  - [x] Create run record with status "running" and start timestamp in active SQLite DB
  - [x] Publish run.requested event to Redis stream ml:run-events with required envelope
- [x] Task 2: Implement run status updates from ML events (AC: 4)
  - [x] Add consumer for run.completed and run.failed events with idempotent handling
  - [x] Update run status and end timestamp in active SQLite DB
- [x] Task 3: Expose run status for UI
  - [x] Implement GET /api/runs/{id} and response DTOs in camelCase
  - [x] Add run summary/report endpoint if needed for run summary bar
- [x] Task 4: Wire UI run controls and status display
  - [x] Add or extend RunControls and RunStatus UI under frontend/src/features/runs
  - [x] Show run summary bar (last run time, new count, relevant count, quota remaining)
  - [x] Surface run status or quota warnings in detail footer area
- [x] Task 5: Tests and observability
  - [x] Add API tests for run trigger, run-in-progress error, and event consumption
  - [x] Add ML tests for event publishing format
  - [x] Add frontend tests for run status and error states

### Review Follow-ups (AI)

- [ ] [AI-Review][High] Implement run summary metrics + API response fields; summary bar still placeholders and no API support. `frontend/src/features/runs/components/RunStatus.tsx:40` `api/src/main/java/com/jobato/api/controller/RunController.java:22` `api/src/main/java/com/jobato/api/dto/RunResponse.java:3`
- [ ] [AI-Review][High] Fix story documentation mismatch: File List claims changes but git shows no modified files; reconcile story with repo state. `/_bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md:150`
- [ ] [AI-Review][Medium] Make run-in-progress guard atomic to prevent concurrent POSTs creating multiple running runs (transactional lock/DB constraint). `api/src/main/java/com/jobato/api/service/RunService.java:38` `api/src/main/java/com/jobato/api/repository/RunRepository.java:39`
- [ ] [AI-Review][Medium] Update Redis Streams consumption to use consumer groups + last delivered ID; current config replays from 0-0. `api/src/main/java/com/jobato/api/config/RunEventStreamConfig.java:32`
- [ ] [AI-Review][Medium] Align SQLite JDBC version to architecture (3.51.2). `api/build.gradle:29`
- [ ] [AI-Review][Low] Add RFC 7807 `type` URI to problem responses for consistency. `api/src/main/java/com/jobato/api/controller/RunExceptionHandler.java:16`
- [ ] [AI-Review][Low] Extend tests to assert run.requested envelope fields/stream usage. `api/src/test/java/com/jobato/api/controller/RunControllerTest.java:92`

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

### Implementation Plan

- Store run lifecycle state in active SQLite via ActiveRunDatabase and RunRepository; trigger runs via RunService and publish run.requested events to Redis Streams.
- Consume run.completed/run.failed events from Redis Streams and apply idempotent status updates in RunEventsConsumer.
- Expose run status via GET /api/runs/{id}; defer additional summary endpoints until run summary metrics land.
- Add a runs feature module with RunControls + RunStatus, including a summary bar scaffold and status notice banner.
- Validate run lifecycle flow with API, ML, and frontend tests aligned to event envelopes and status UI.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Implemented run trigger flow with SQLite-backed run records, RFC 7807 run-in-progress handling, and Redis run.requested publishing.
- Added Redis Stream consumer wiring with idempotent run status updates for run.completed/run.failed events.
- Implemented GET /api/runs/{id} for UI polling; no additional summary endpoint needed yet.
- Built the Runs UI with controls, status polling, and a summary bar scaffold under frontend/src/features/runs.
- Added API, ML, and frontend tests for run lifecycle events and UI states.
- Tests run: `./gradlew test`, `npm test`, `.venv/bin/python -m pytest`.

### File List

- _bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- api/build.gradle
- api/src/main/java/com/jobato/api/controller/RunController.java
- api/src/main/java/com/jobato/api/controller/RunExceptionHandler.java
- api/src/main/java/com/jobato/api/config/RunEventStreamConfig.java
- api/src/main/java/com/jobato/api/dto/RunResponse.java
- api/src/main/java/com/jobato/api/messaging/RunEventEnvelope.java
- api/src/main/java/com/jobato/api/messaging/RunEventsConsumer.java
- api/src/main/java/com/jobato/api/messaging/RedisRunEventPublisher.java
- api/src/main/java/com/jobato/api/messaging/RunEventPublisher.java
- api/src/main/java/com/jobato/api/model/RunRecord.java
- api/src/main/java/com/jobato/api/repository/ActiveRunDatabase.java
- api/src/main/java/com/jobato/api/repository/RunRepository.java
- api/src/main/java/com/jobato/api/service/RunInProgressException.java
- api/src/main/java/com/jobato/api/service/RunNotFoundException.java
- api/src/main/java/com/jobato/api/service/RunService.java
- api/src/test/java/com/jobato/api/controller/RunControllerTest.java
- api/src/test/java/com/jobato/api/messaging/RunEventsConsumerTest.java
- api/src/test/java/com/jobato/api/service/RunServiceTest.java
- frontend/src/app/AppLayout.tsx
- frontend/src/app/router.tsx
- frontend/src/features/runs/api/runs-api.ts
- frontend/src/features/runs/components/RunControls.css
- frontend/src/features/runs/components/RunControls.tsx
- frontend/src/features/runs/components/RunPage.css
- frontend/src/features/runs/components/RunPage.tsx
- frontend/src/features/runs/components/RunStatus.css
- frontend/src/features/runs/components/RunStatus.test.tsx
- frontend/src/features/runs/components/RunStatus.tsx
- frontend/src/features/runs/hooks/use-runs.ts
- frontend/src/features/runs/index.ts
- ml/app/schemas/__init__.py
- ml/app/schemas/events.py
- ml/tests/test_events.py
