# Story 1.2: Manage query strings

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to create and edit query strings,
so that I can control the job searches I care about.

## Acceptance Criteria

1. Given a valid query string, when I add it, then it is persisted and available for runs and appears in the enabled queries list by default.
2. Given an existing query, when I edit it, then the updated query is stored and used on subsequent runs and existing run history remains unchanged.
3. Given an existing query, when I disable it, then it is excluded from run generation and remains available for re-enable without losing its contents.
4. Given a duplicate query text, when I try to add it, then the system rejects the duplicate with a clear validation error and no additional query entry is created.

## Tasks / Subtasks

- [ ] Define query config schema and persistence rules (AC: 1, 2, 3, 4)
  - [ ] Specify `config/queries.yaml` schema (id, text, enabled, createdAt, updatedAt) and normalization rules for duplicate detection
  - [ ] Implement atomic read/write with validation and stable ordering
  - [ ] Default new queries to enabled=true; disable keeps record without data loss
- [ ] Implement query management API (AC: 1, 2, 3, 4)
  - [ ] GET `/api/queries` returns list with enabled state
  - [ ] POST `/api/queries` validates duplicates and persists
  - [ ] PUT/PATCH `/api/queries/{id}` edits text and enabled state without mutating run history
  - [ ] Return RFC 7807 Problem Details for validation errors
- [ ] Build minimal query management UI (AC: 1, 2, 3, 4)
  - [ ] Query list with add/edit and enable/disable controls
  - [ ] Use TanStack Query for fetch/mutations; invalidate list on success
  - [ ] Keep UI minimal; avoid complex filtering/configuration surfaces
- [ ] Add targeted tests (AC: 1, 2, 3, 4)
  - [ ] API unit tests for duplicate detection, enable/disable, and update behavior
  - [ ] Frontend tests for add/edit/disable flows (if UI is in scope)

## Dev Notes

### Developer Context

- Query strings are core inputs for run generation; persist in `config/queries.yaml` and default new entries to enabled=true.
- Updates must not rewrite existing run history; treat query changes as future-run inputs only.
- UX guidance warns against complex configuration UI and explicitly says no configuration in the app, while architecture maps queries to frontend features; keep UI minimal and call out this decision if needed.

### Technical Requirements

- Config files are external; do not store query strings in SQLite.
- API uses REST + JSON under `/api`; responses use camelCase JSON and RFC 7807 Problem Details for validation errors.
- Duplicate detection should normalize query text (trim and collapse whitespace; apply case-insensitive compare).
- Query model must include stable identifiers and enabled state; prefer `id`, `text`, `enabled`, `createdAt`, `updatedAt` in `config/queries.yaml`.
- Disabled queries must remain persisted and excluded from run generation until re-enabled.

### Architecture Compliance

- Query configuration lives in `config/queries.yaml` on the shared config volume; keep it external to code and SQLite.
- API code belongs under `api/src/main/java/com/jobato/api/{controller,service,repository,model,dto}`; use JDBC + Flyway only when data is stored in SQLite (not for queries).
- Follow naming rules: camelCase JSON fields, snake_case DB identifiers, plural REST resources.
- Keep service boundaries: frontend talks to API only; ML consumption of queries is via config file, not direct API coupling.

### Library and Framework Requirements

- Frontend uses React Router 7.13.0 and TanStack Query 5.90.20 for server state; no ad-hoc caching.
- API uses Spring Boot 4.0.2.RELEASE (Java 17) with SpringDoc 3.0.1; use ProblemDetail for RFC 7807 error responses.
- Keep react-window 2.2.6 available for long lists if needed, but do not add extra UI libraries unless required.

### Testing and Verification Requirements

- API unit tests in `api/src/test/java` for duplicate detection, validation errors, and update/disable behavior.
- Frontend tests co-located `*.test.tsx` for query add/edit/disable flows if UI is implemented.
- No E2E tests in MVP; keep checks lightweight and local.

### Previous Story Intelligence

- Story 1.1 established the scaffold-only baseline; keep service boundaries strict (frontend/api/ml) and avoid introducing business logic outside this story's scope.
- Stack versions are pinned; do not upgrade React Router, TanStack Query, Spring Boot, or FastAPI versions.
- Config and data volumes are core architecture; keep query config in `config/` and avoid writing configs into SQLite.
- Prior story noted missing validation workflow file (`_bmad/core/tasks/validate-workflow.xml`); expect validation step to fail unless provided.

### Git Intelligence Summary

- Recent commits only touch planning and story artifacts; no application code patterns exist yet.
- Sprint status and Story 1.1 were the last recorded changes; expect to establish first query feature patterns in this story.

### Latest Technical Notes

- Spring MVC supports returning `ProblemDetail`/`ErrorResponse` for RFC 9457-style error responses; align its usage with RFC 7807 requirements in this project.
- TanStack Query React docs emphasize setting up a `QueryClient`/`QueryClientProvider` and using `useQuery` with `queryKey` and `queryFn` plus pending/error handling; apply this pattern for query list reads.

### Project Context Reference

- Follow project-context rules for stack versions, naming conventions, and API JSON casing.
- Keep configs external and avoid ad-hoc caches; use TanStack Query for server data and `config/` for persisted query definitions.

### Project Structure Notes

- Frontend: `frontend/src/features/queries` with `api/`, `components/`, `hooks/` per architecture mapping.
- API: `QueryController`, `QueryService`, `QueryRepository` (file-backed) under `com.jobato.api.*`.
- Config: `config/queries.yaml` is the source of truth for query definitions.
- Conflict to resolve: UX spec states no configuration in the app; if enforced, limit UI scope or implement file-based management only.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 1: Configure Search Scope]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns]
- [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Anti-Patterns to Avoid]
- [External: https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/return-types.html]
- [External: https://tanstack.com/query/latest/docs/framework/react/overview]

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- Validation workflow file not found: `_bmad/core/tasks/validate-workflow.xml`

### Completion Notes List

- Story drafted from epics, architecture, PRD, UX, and project-context sources.
- Previous story and git history reviewed for constraints and patterns.
- Web research referenced for Spring ProblemDetail and TanStack Query basics.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- Sprint status updated to ready-for-dev.

### File List

- _bmad-output/implementation-artifacts/1-2-manage-query-strings.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
