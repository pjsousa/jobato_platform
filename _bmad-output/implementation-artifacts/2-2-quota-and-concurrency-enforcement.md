# Story 2.2: Quota and concurrency enforcement

Status: review
Story Key: 2-2-quota-and-concurrency-enforcement
Epic: 2 - Run and Capture Results

## Story

As a user,
I want runs to respect concurrency and daily quota limits,
so that I avoid exceeding API limits.

## Acceptance Criteria

1. Given configured concurrency and daily quota, when a run executes, then concurrent query execution does not exceed the configured limit and the quota counter is updated as calls are made.
2. Given the daily quota is already reached, when I trigger a run, then the system blocks the run and returns a quota-reached error.
3. Given the quota is reached mid-run, when additional calls would exceed it, then the system stops issuing new calls and the run is marked partial with a quota-reached reason.

## Tasks / Subtasks

- [x] Task 1: Define quota and concurrency configuration (AC: 1, 2, 3)
  - [x] Ensure quota settings live in external config (config/quota.yaml) and are mounted into services
  - [x] Define daily quota limit, concurrency limit, and reset policy inputs
- [x] Task 2: Enforce concurrency and quota in ML run pipeline (AC: 1, 3)
  - [x] Limit concurrent query execution to the configured max
  - [x] Increment quota counter per external API call and persist per run/day
  - [x] When quota is reached mid-run, stop issuing new calls and mark run status partial with reason quota-reached
- [x] Task 3: Block runs when quota is already reached (AC: 2)
  - [x] Add pre-run quota check in RunService before creating the run record
  - [x] Return RFC 7807 Problem Details with a clear quota-reached message and errorCode
- [x] Task 4: Propagate partial status to API and UI (AC: 3)
  - [x] Emit run completion event with status partial and reason (do not introduce new event types)
  - [x] Update run status storage and DTOs to include partial and reason
  - [x] Show quota-reached warning in run summary bar and detail footer
- [x] Task 5: Tests and observability
  - [x] API tests for quota-reached block and partial status persistence
  - [x] ML tests for concurrency cap and quota stop behavior
  - [x] Frontend tests for quota-reached warning and partial status display

### Review Follow-ups (AI)

- [ ] [AI-Review][HIGH] Ensure quota enforcement re-checks remaining quota during concurrent execution to prevent exceeding daily limit when multiple runs share quota store. [ml/app/pipelines/run_pipeline.py:35]
- [ ] [AI-Review][HIGH] Complete RFC 7807 problem details for quota-reached errors (set `type` and expand tests to assert required fields). [api/src/main/java/com/jobato/api/controller/RunExceptionHandler.java:35]
- [ ] [AI-Review][HIGH] Validate/handle malformed `run.completed` payloads so partial status isn't silently downgraded. [api/src/main/java/com/jobato/api/messaging/RunEventsConsumer.java:59]
- [ ] [AI-Review][MEDIUM] Replace JSON-in-YAML with actual YAML in `config/quota.yaml` and tests to match operator expectations. [config/quota.yaml:1]
- [ ] [AI-Review][MEDIUM] Establish schema/migration contract for `quota_usage` DB access and avoid silent zero-usage fallback on missing table. [api/src/main/java/com/jobato/api/repository/QuotaUsageRepository.java:23]
- [ ] [AI-Review][LOW] Add explicit partial/quota-reached detail footer copy per UX guidance in run status UI. [frontend/src/features/runs/components/RunStatus.tsx:82]

## Dev Notes

### Developer Context

- Epic 2 focuses on reliable run orchestration with strict quota and concurrency limits to avoid API overages. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2]
- Quota enforcement is a critical risk mitigation area alongside caching and deterministic query ordering. [Source: _bmad-output/planning-artifacts/prd.md#Risk Mitigation Strategy]
- UX requires clear run status and warning/error states for quota reached and zero results. [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Executive Summary, _bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns]
- Quota is a cross-cutting concern; config is external under config/ and ML quota logic lives in ml/app/services/quota.py. [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns, _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]

### Technical Requirements

- Enforce concurrency limit for query execution using the configured global setting; do not exceed it at any time. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2, _bmad-output/planning-artifacts/prd.md#Run Orchestration]
- Update quota counter as external API calls are made; quota must prevent additional calls once the limit is reached. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2]
- If quota is already reached at run trigger time, block the run and return RFC 7807 Problem Details with a clear quota-reached message. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2, _bmad-output/planning-artifacts/architecture.md#API Response Formats]
- If quota is reached mid-run, stop issuing new calls and mark the run as partial with reason quota-reached. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2]
- Use existing run.* event types and the standard event envelope; do not create new event types without an architecture update. [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns, _bmad-output/project-context.md#Language-Specific Rules]
- Do not implement caching in this story; ensure quota logic is compatible with future cache short-circuiting in Story 2.5. [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5]

### Architecture Compliance

- REST + JSON under /api with RFC 7807 Problem Details for errors; camelCase JSON only. [Source: _bmad-output/planning-artifacts/architecture.md#API and Communication Patterns, _bmad-output/project-context.md#Critical Implementation Rules]
- Redis Streams event flow: API publishes run.requested; ML publishes run.completed/run.failed; consumers must be idempotent. [Source: _bmad-output/planning-artifacts/architecture.md#Integration Points, _bmad-output/planning-artifacts/architecture.md#Event System Patterns]
- API writes to active SQLite only; ML writes to a new DB copy then swaps pointer and stops writing to active DB. [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture, _bmad-output/project-context.md#Critical Implementation Rules]
- Config is external (config/); do not embed config in SQLite or code. [Source: _bmad-output/planning-artifacts/architecture.md#Data Boundaries, _bmad-output/project-context.md#Language-Specific Rules]

### Library/Framework Requirements

- API: Spring Boot 3.5.10.RELEASE (Java 17), SpringDoc 2.7.0, Flyway 12.0.0, Micrometer 1.16.2. [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions, _bmad-output/project-context.md#Technology Stack]
- Messaging: Redis Streams on Redis 8.4.x. [Source: _bmad-output/planning-artifacts/architecture.md#API and Communication Patterns]
- Frontend: React Router 7.13.0, TanStack Query 5.90.20, react-window 2.2.6. [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions]
- ML: FastAPI with SQLAlchemy 2.0.46 + Alembic 1.18.3 for SQLite runs DB. [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]

### File Structure Requirements

- Quota config should live in config/quota.yaml and be mounted into containers. [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]
- ML quota/concurrency logic in ml/app/services/quota.py and run orchestration in ml/app/pipelines/run_pipeline.py. [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- API run orchestration in com.jobato.api.controller.RunController, service.RunService, repository.RunRepository; event consumption in messaging.RunEventsConsumer. [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]
- Frontend run status UI in frontend/src/features/runs (RunControls, RunStatus, hooks/use-runs). [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries]

### Testing Requirements

- API tests in api/src/test/java: quota-reached pre-run block and partial status persistence. [Source: _bmad-output/project-context.md#Testing Rules]
- ML tests in ml/tests: concurrency cap and quota stop behavior; event payload includes required envelope fields. [Source: _bmad-output/project-context.md#Testing Rules]
- Frontend tests co-located in frontend/src/features/runs: quota-reached warning, run summary updates, partial status UI. [Source: _bmad-output/project-context.md#Testing Rules]

### Previous Story Intelligence

- Story 2.1 established run.requested event publishing, run completion handling, and RFC 7807 error patterns for run-in-progress. Align quota errors with the same response conventions. [Source: _bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md#Technical Requirements]
- Run summary bar and detail footer are expected UI surfaces for status and warnings; reuse those patterns for quota-reached messaging. [Source: _bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md#Technical Requirements]
- Event envelope fields (eventId, eventType, eventVersion, occurredAt, runId, payload) are mandatory; keep dot-lowercase eventType. [Source: _bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md#Technical Requirements]

### Git Intelligence Summary

- Recent commits touched ML and API runtime configuration and Redis reachability; keep quota checks compatible with existing Redis connectivity assumptions. [Source: git log]
- Docker Compose healthchecks were added; ensure quota/config loading does not break container health status. [Source: git log]

### Latest Tech Information

- Spring Boot latest GA is 4.0.2; project remains pinned to 3.5.10 for Java 17 compatibility. [Source: https://github.com/spring-projects/spring-boot/releases]
- Redis latest 8.4.x GA is 8.4.1 with security fixes; stay on 8.4.x line. [Source: https://github.com/redis/redis/releases]
- FastAPI latest is 0.128.5; ensure Pydantic v2 compatibility if upgrading. [Source: https://github.com/fastapi/fastapi/releases]
- React Router latest is 7.13.0; pinned version matches latest. [Source: https://github.com/remix-run/react-router/releases]
- TanStack Query continues 5.9x releases; keep 5.90.20 unless upgrading with review. [Source: https://github.com/TanStack/query/releases]

### Project Context Reference

- Enforce camelCase JSON in API responses; no snake_case. [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- Use TanStack Query for server data; no ad-hoc caches. [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- Internal endpoints must require X-Jobato-Api-Key. [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- ML must never write to active DB after pointer swap. [Source: _bmad-output/project-context.md#Critical Implementation Rules]

### Story Completion Status

- Status set to ready-for-dev.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

### References

- _bmad-output/planning-artifacts/epics.md#Story 2.2
- _bmad-output/planning-artifacts/prd.md#Run Orchestration
- _bmad-output/planning-artifacts/prd.md#Risk Mitigation Strategy
- _bmad-output/planning-artifacts/architecture.md#Event System Patterns
- _bmad-output/planning-artifacts/architecture.md#Project Structure and Boundaries
- _bmad-output/planning-artifacts/ux-design-specification.md#Run Summary Bar
- _bmad-output/project-context.md#Critical Implementation Rules
- https://github.com/spring-projects/spring-boot/releases
- https://github.com/redis/redis/releases
- https://github.com/fastapi/fastapi/releases
- https://github.com/remix-run/react-router/releases
- https://github.com/TanStack/query/releases

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- None

### Implementation Plan

- Define config/quota.yaml with dailyLimit, concurrencyLimit, and resetPolicy inputs.
- Add quota config loaders in API and ML with unit tests.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added config/quota.yaml plus API/ML quota config loaders with validation and tests.
- Implemented ML quota store + run pipeline with concurrency cap and quota-stop behavior; added pipeline tests.
- Added API pre-run quota guard with RFC 7807 QUOTA_REACHED responses and quota usage lookup.
- Propagated partial run status + reason through ML events, API storage/DTOs, and UI warnings.
- Adjusted AllowlistForm remounting to satisfy react-hooks/set-state-in-effect lint rule.

### File List

- _bmad-output/implementation-artifacts/2-2-quota-and-concurrency-enforcement.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- api/src/main/java/com/jobato/api/config/QuotaConfigRepository.java
- api/src/main/java/com/jobato/api/config/QuotaResetPolicy.java
- api/src/main/java/com/jobato/api/config/QuotaSettings.java
- api/src/test/java/com/jobato/api/config/QuotaConfigRepositoryTest.java
- config/quota.yaml
- api/src/main/java/com/jobato/api/controller/RunExceptionHandler.java
- api/src/main/java/com/jobato/api/repository/QuotaUsageRepository.java
- api/src/main/java/com/jobato/api/service/QuotaReachedException.java
- api/src/main/java/com/jobato/api/service/QuotaService.java
- api/src/main/java/com/jobato/api/service/RunService.java
- api/src/test/java/com/jobato/api/controller/RunControllerTest.java
- api/src/test/java/com/jobato/api/service/RunServiceTest.java
- api/src/main/java/com/jobato/api/dto/RunResponse.java
- api/src/main/java/com/jobato/api/messaging/RunEventsConsumer.java
- api/src/main/java/com/jobato/api/model/RunRecord.java
- api/src/main/java/com/jobato/api/repository/ActiveRunDatabase.java
- api/src/main/java/com/jobato/api/repository/RunRepository.java
- api/src/test/java/com/jobato/api/messaging/RunEventsConsumerTest.java
- ml/app/services/__init__.py
- ml/app/services/quota.py
- ml/app/pipelines/__init__.py
- ml/app/pipelines/run_pipeline.py
- ml/tests/test_quota_config.py
- ml/tests/test_run_pipeline.py
- frontend/src/features/runs/api/runs-api.ts
- frontend/src/features/runs/components/RunPage.tsx
- frontend/src/features/runs/components/RunStatus.css
- frontend/src/features/runs/components/RunStatus.test.tsx
- frontend/src/features/runs/components/RunStatus.tsx
- frontend/src/features/runs/hooks/use-runs.ts
- frontend/src/features/allowlist/components/AllowlistForm.tsx
- frontend/src/features/allowlist/components/AllowlistPage.tsx
