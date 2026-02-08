# Story 1.4: Generate per-site query combinations

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want the system to combine enabled queries and allowlisted domains,
so that each run executes per-site searches.

## Acceptance Criteria

1. Given enabled queries and allowlisted domains, when a run is initiated, then the system generates all query x domain combinations and only enabled queries and domains are included.
2. Given a disabled query or domain, when a run is initiated, then combinations including it are not generated and the run uses only enabled inputs.
3. Given no enabled queries or domains, when a run is initiated, then the system returns a clear error and does not proceed, and the user is prompted to add or enable queries and domains.

## Tasks / Subtasks

- [x] Define the per-site query combination model and ordering rules (AC: 1, 2)
  - [x] Confirm normalized inputs from `config/queries.yaml` and `config/allowlists.yaml` (reuse Story 1.2/1.3 rules).
  - [x] Decide deterministic ordering (queries order first, then allowlist order) and dedupe strategy after normalization.
- [x] API: implement a `RunInputService` to build enabled combinations (AC: 1, 2, 3)
  - [x] Load enabled queries and allowlists from their repositories; apply normalization and filtering.
  - [x] Generate `searchQuery` using `site:<domain> <queryText>` while retaining raw query/domain fields.
  - [x] Validate empty enabled inputs and throw RFC 7807 Problem Detail with errorCode `NO_ENABLED_INPUTS`.
- [x] Wiring: expose combinations to run initiation (AC: 1, 2, 3)
  - [x] `RunService` (Story 2.1) should call `RunInputService` before publishing `run.requested`.
  - [x] Prefer including combinations in the event payload so ML does not re-read config files.
- [x] Tests: add service-level unit tests (AC: 1, 2, 3)
  - [x] Enabled/disabled filtering, empty inputs error, duplicate normalization, deterministic ordering.

### Review Follow-ups (AI)

- [ ] [AI-Review][High] Wire run initiation to include run inputs when publishing `run.requested`; current service only builds a payload [api/src/main/java/com/jobato/api/service/RunService.java:17]
- [ ] [AI-Review][High] Add test coverage for empty enabled domains (AC3) so NO_ENABLED_INPUTS is raised when allowlists are empty [api/src/test/java/com/jobato/api/service/RunInputServiceTest.java:95]
- [ ] [AI-Review][High] Reconcile story File List with git working tree; story lists changes but git is clean [_bmad-output/implementation-artifacts/1-4-generate-per-site-query-combinations.md:173]
- [ ] [AI-Review][Medium] Guard against empty/invalid domains after normalization to avoid `site:` with blank domain [api/src/main/java/com/jobato/api/service/RunInputNormalizer.java:52]
- [ ] [AI-Review][Medium] Add ProblemDetail handling for `QueryValidationException` to avoid 500s on invalid config inputs [api/src/main/java/com/jobato/api/service/RunInputNormalizer.java:31] [api/src/main/java/com/jobato/api/controller/RunInputExceptionHandler.java:15]

## Dev Notes

### Developer Context

- This story defines the canonical generation of per-site queries by combining enabled query strings with enabled allowlisted domains.
- The combination list is the input to run execution and caching; keep ordering stable and deterministic for reproducibility and quota accounting.
- Source of truth is `config/queries.yaml` and `config/allowlists.yaml` on the shared config volume; reuse normalization rules from Stories 1.2 and 1.3.
- If there are zero enabled queries or domains, fail fast with a clear, user-facing error (RFC 7807 in API; `run.failed` event if emitted by ML).
- When constructing per-site searches for Google, use the `site:` operator (`site:example.com <query>`), while preserving the raw query text for display/logging.
- Do not introduce new storage; this is a pure combination/validation step that feeds run orchestration in Epic 2.

### Technical Requirements

- Inputs: `config/queries.yaml` and `config/allowlists.yaml` are the only sources of truth.
- Only enabled entries are included; disabled queries/domains are excluded from combinations.
- Normalize inputs consistently:
  - Query text: trim, collapse whitespace, case-insensitive for dedupe (per Story 1.2).
  - Domain: trim, lowercase, remove trailing dot; reject schemes/paths (per Story 1.3).
- Generate combinations deterministically (stable ordering by query order then allowlist order).
- Output shape (internal DTO): `queryId`, `queryText`, `domain`, `searchQuery` (with `site:` prefix), and `enabled` is not propagated.
- Fail fast when either enabled list is empty; return RFC 7807 Problem Detail with a clear message and errorCode `NO_ENABLED_INPUTS`.

### Architecture Compliance

- Keep configuration in `config/` (mounted volume); do not store combinations in SQLite.
- Use Spring Boot service layer (`com.jobato.api.service`) and repositories from Stories 1.2/1.3 for loading config.
- JSON must remain camelCase; errors must use RFC 7807 Problem Details.
- If ML needs combinations, pass them via `run.requested` event (Redis Streams) rather than duplicating config parsing.

### Library / Framework Requirements

- API: Spring Boot 4.0.2.RELEASE (Java 17) with ProblemDetail for validation errors.
- Do not add new libraries for YAML parsing; reuse the existing config parsing approach from queries/allowlists.

### File Structure Requirements

- API: `api/src/main/java/com/jobato/api/service/RunInputService.java`
- API DTO: `api/src/main/java/com/jobato/api/dto/RunInput.java`
- API wiring: `api/src/main/java/com/jobato/api/service/RunService.java` (integration in Story 2.1)
- Tests: `api/src/test/java/com/jobato/api/service/RunInputServiceTest.java`
- Config sources: `config/queries.yaml`, `config/allowlists.yaml`

### Testing Requirements

- Unit tests for:
  - Enabled-only filtering and deterministic ordering.
  - Empty enabled queries/domains -> RFC 7807 error with `NO_ENABLED_INPUTS`.
  - Duplicate normalization across query text and domains.
- No E2E tests in MVP.

### Previous Story Intelligence

- Story 1.2: Query schema expects `id`, `text`, `enabled`, `createdAt`, `updatedAt`; duplicate detection is normalized and case-insensitive.
- Story 1.3: Domain validation is strict (no scheme/path); conflict noted between UX spec (“no configuration in app”) and architecture (frontend features). Keep UI minimal.

### Git Intelligence Summary

- Recent commits only scaffolded services and created story artifacts; no established code patterns for run inputs yet.

### Latest Tech Information

- Spring Boot GitHub releases list `v4.0.2` as the latest release (Jan 22, 2026); keep the project pinned to 4.0.2.RELEASE unless architecture updates. [Source: https://github.com/spring-projects/spring-boot]
- FastAPI release notes list `0.128.4` as the latest release; no upgrade planned without architecture change. [Source: https://fastapi.tiangolo.com/release-notes/]
- Redis release notes show Redis Open Source `v8.6.0` (Jan 2026) and `v8.4.0` (Nov 2025). Project pins 8.4; keep until architecture updates. [Source: https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/]
- React Router changelog shows `v7.13.0` (Jan 23, 2026), matching the pinned version. [Source: https://reactrouter.com/start/start/changelog]

### Project Structure Notes

- API: `RunInputService` in `com.jobato.api.service`; DTO in `com.jobato.api.dto`.
- Config: query/allowlist files live in `config/` and are mounted into containers.
- Integration point: `RunService` should call `RunInputService` before `run.requested` is emitted (Story 2.1).
- Tests: `api/src/test/java/com/jobato/api/service/RunInputServiceTest.java`.

### References

- Story requirements: `/_bmad-output/planning-artifacts/epics.md#Story 1.4`
- FR mapping: `/_bmad-output/planning-artifacts/prd.md#Functional Requirements`
- Architecture patterns and event envelope: `/_bmad-output/planning-artifacts/architecture.md#Communication Patterns`
- Project rules and stack versions: `/_bmad-output/project-context.md#Technology Stack & Versions`
- Query/allowlist config rules: `/_bmad-output/implementation-artifacts/1-2-manage-query-strings.md` and `/_bmad-output/implementation-artifacts/1-3-manage-allowlist-domains.md`
- UX constraint on configuration UI: `/_bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns`
- External version references:
  - https://github.com/spring-projects/spring-boot
  - https://fastapi.tiangolo.com/release-notes/
  - https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/
  - https://reactrouter.com/start/start/changelog

### Project Context Reference

- `/_bmad-output/project-context.md#Technology Stack & Versions`
- `/_bmad-output/project-context.md#Critical Implementation Rules`

### Story Completion Status

- Status: in-progress
- Completion note: Review found issues; see Review Follow-ups (AI).

### Open Questions

- Should `run.requested` include the full combination list, or should ML re-read config on receipt?
- Do we want to strip `www.` during domain normalization, or preserve it as a distinct allowlist entry?
- Should the combination DTO include a stable `combinationId` for logging and caching?

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- create-story workflow (CS 1.4, yolo)
- Validation workflow file missing: `/_bmad/core/tasks/validate-workflow.xml`
- Tests: `./gradlew test --tests "com.jobato.api.service.RunInputNormalizerTest"` (api)
- Tests: `./gradlew test` (api)
- Tests: `./gradlew test --tests "com.jobato.api.service.RunInputServiceTest"` (api)
- Tests: `./gradlew test` (api)
- Tests: `./gradlew test --tests "com.jobato.api.service.RunServiceTest"` (api)
- Tests: `./gradlew test` (api)
- Tests: `./gradlew test --tests "com.jobato.api.service.RunInputServiceTest"` (api)
- Tests: `./gradlew test` (api)
- Tests: `./gradlew test` (api)

### Implementation Plan

- Introduce RunInput DTO and normalization helper for enabled query/domain dedupe with stable ordering.
- Build RunInputService to assemble combinations with RFC 7807 error handling for empty inputs.
- Add RunService wiring to expose run inputs in a run.requested payload DTO.
- Expand RunInputService tests to cover filtering, dedupe, ordering, and empty-input errors.
### Completion Notes List

- Story drafted from epics, PRD, architecture, UX, and project-context sources.
- Previous story and git history reviewed for constraints and patterns.
- Latest tech versions checked against official release notes.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added RunInput DTO plus normalization helper for enabled query/domain dedupe and ordering; added unit tests for normalization.
- Implemented RunInputService for per-site combinations with ProblemDetail error handling and service-level test.
- Added RunService payload wiring so run initiation can include run inputs without re-reading config.
- Added RunInputService coverage for filtering, dedupe, deterministic ordering, and empty input errors.
### File List

- `/_bmad-output/implementation-artifacts/1-4-generate-per-site-query-combinations.md`
- `/_bmad-output/implementation-artifacts/sprint-status.yaml`
- `api/src/main/java/com/jobato/api/dto/RunInput.java`
- `api/src/main/java/com/jobato/api/dto/RunRequestedPayload.java`
- `api/src/main/java/com/jobato/api/controller/RunInputExceptionHandler.java`
- `api/src/main/java/com/jobato/api/service/NoEnabledInputsException.java`
- `api/src/main/java/com/jobato/api/service/RunInputService.java`
- `api/src/main/java/com/jobato/api/service/RunInputNormalizer.java`
- `api/src/main/java/com/jobato/api/service/RunService.java`
- `api/src/test/java/com/jobato/api/service/RunInputServiceTest.java`
- `api/src/test/java/com/jobato/api/service/RunInputNormalizerTest.java`
- `api/src/test/java/com/jobato/api/service/RunServiceTest.java`

### Change Log

- 2026-02-08: Implemented run input combinations, run request payload wiring, and service tests for Story 1.4.
