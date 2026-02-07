# Story 1.3: Manage allowlist domains

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to create, edit, and disable allowlisted domains,
so that searches run only on approved sites.

## Acceptance Criteria

1. Given a valid domain, when I add it, then it is persisted and available for runs, and it appears enabled by default.
2. Given an existing domain, when I edit it, then the updated domain is stored and used for subsequent runs, and existing run history remains unchanged.
3. Given an existing domain, when I disable it, then it is excluded from run generation and remains available for re-enable without losing its contents.
4. Given an invalid domain format, when I try to add it, then the system rejects it with a clear validation error and no allowlist entry is created.

## Tasks / Subtasks

- [x] Define allowlist entry shape and persistence in `config/allowlists.yaml` (domain + enabled), including normalization rules and atomic read/write. (AC: 1, 3, 4)
  - [x] Decide uniqueness key (domain string) and normalization (trim, lowercase, no scheme/path).
- [x] API: implement allowlist list/create/update/enable-disable in `AllowlistController/Service/Repository` under `/api/allowlists`. (AC: 1-4)
  - [x] Validate domain format and duplicates; return RFC 7807 Problem Details for errors.
  - [x] Ensure edits only affect future runs (no backfill or history mutation).
- [x] Frontend: add allowlist management UI under `frontend/src/features/allowlist` with list + add/edit + enable/disable, backed by TanStack Query. (AC: 1-3)
  - [x] Keep UI minimal and keyboard-accessible; avoid complex configuration flows.
- [x] Tests: add API tests under `api/src/test/java` for validation/duplication/enable-disable; add co-located UI tests as needed. (AC: 1-4)

### Review Follow-ups (AI)

- [ ] [AI-Review][High] Align Spring Boot/SpringDoc versions with architecture (4.0.2.RELEASE / 3.0.1) [api/build.gradle:3] [api/build.gradle:25]
- [ ] [AI-Review][High] Story File List does not match git working tree; reconcile story documentation with actual changes [/_bmad-output/implementation-artifacts/1-3-manage-allowlist-domains.md:118]
- [ ] [AI-Review][Medium] Guard null/empty create request body to return RFC 7807 instead of 500 [api/src/main/java/com/jobato/api/service/AllowlistService.java:24] [api/src/main/java/com/jobato/api/controller/AllowlistController.java:34]
- [ ] [AI-Review][Medium] YAML persistence drops unknown keys/comments; preserve or explicitly document ownership of `config/allowlists.yaml` [api/src/main/java/com/jobato/api/repository/AllowlistRepository.java:69] [api/src/main/java/com/jobato/api/repository/AllowlistRepository.java:102]
- [ ] [AI-Review][Low] Confirm configuration UI is intended for MVP; otherwise move to admin/CLI flow [frontend/src/features/allowlist/components/AllowlistPage.tsx:54]
- [ ] [AI-Review][Low] Avoid empty state during loading; show loading skeleton or suppress empty state until query resolves [frontend/src/features/allowlist/components/AllowlistTable.tsx:10] [frontend/src/features/allowlist/components/AllowlistPage.tsx:83]

## Dev Notes

- Epic 1 scope: this story establishes allowlist CRUD + enable/disable; run generation uses enabled allowlists in Story 1.4.
- Storage source of truth is `config/allowlists.yaml` (shared `config/` volume); keep persistence local-first.
- Architecture maps allowlist feature to both frontend and API, but UX spec says “no configuration in UI” (conflict). Build a minimal UI unless product direction says config-only.
- Validation must be strict and user-facing: no scheme/path, reject invalid domain format with RFC 7807 error.
- Keep query + allowlist UX and API patterns consistent (Story 1.2 and 1.3 should mirror list/create/edit/disable flows).

### Technical Requirements

- Persist allowlists in `config/allowlists.yaml` with `domain` and `enabled` fields; treat domain as unique key unless an explicit id is added.
- Normalize domain inputs (trim, lowercase, remove trailing dot); reject protocols, paths, ports, and wildcards unless explicitly allowed.
- Implement soft-disable via `enabled: false`; do not delete entries so re-enable is lossless.
- API responses use camelCase JSON and RFC 7807 Problem Details for validation errors; list responses are bare arrays.
- Do not mutate historical run data; changes only affect future run generation.

### Architecture Compliance

- Spring Boot 4.0.2 (Java 17) API with controllers in `com.jobato.api.controller`, services in `service`, repositories in `repository`.
- REST + JSON under `/api`; errors in RFC 7807 format; no wrapper object for list responses.
- Configs live in `config/` mounted volume; do not embed allowlist config inside SQLite.
- Frontend uses React Router + TanStack Query; keep server state in Query (no custom caches).

### Library / Framework Requirements

- Frontend: React Router 7.13.0, TanStack Query 5.90.20; use react-window 2.2.6 only if list size warrants virtualization.
- API: Spring Boot 4.0.2.RELEASE with SpringDoc 3.0.1; validation at controller boundary.
- DB tooling (if needed later): JDBC + Flyway 12.0.0 only (no ORM).

### Testing Requirements

- API: unit tests for domain validation, duplicate handling, enable/disable, and error responses (RFC 7807).
- Frontend: component tests for add/edit form validation and enable/disable toggles; keyboard focus states if UI is built.
- No E2E tests in MVP.

### Previous Story Intelligence

- Previous story file `/_bmad-output/implementation-artifacts/1-2.md` contains template placeholders only; no dev notes or learnings available.

### Git Intelligence Summary

- Recent commits only created planning artifacts and Story 1.1; no codebase patterns or implementation decisions to mirror yet.

### Latest Tech Information

- Use the pinned versions from architecture/project context (React Router 7.13.0, TanStack Query 5.90.20, Spring Boot 4.0.2.RELEASE, SpringDoc 3.0.1, Flyway 12.0.0). Do not upgrade without updating architecture docs.

### Project Structure Notes

- Frontend: `frontend/src/features/allowlist/` with `api/allowlist-api.ts`, `hooks/use-allowlist.ts`, `components/AllowlistTable.tsx`, `components/AllowlistForm.tsx`, `index.ts`.
- API: `api/src/main/java/com/jobato/api/controller/AllowlistController.java`, `service/AllowlistService.java`, `repository/AllowlistRepository.java`, `dto/AllowlistRequest.java`.
- Config: `config/allowlists.yaml` (shared volume).
- Tests: `api/src/test/java/com/jobato/api/...` and co-located frontend tests `*.test.tsx`.

### References

- Story requirements and ACs: `/_bmad-output/planning-artifacts/epics.md#Story 1.3`
- API/structure/patterns: `/_bmad-output/planning-artifacts/architecture.md#Architectural Boundaries`
- UX constraints and interaction guidelines: `/_bmad-output/planning-artifacts/ux-design-specification.md#UX Consistency Patterns`
- Tech stack + rules: `/_bmad-output/project-context.md#Technology Stack & Versions`
- Functional requirements coverage: `/_bmad-output/planning-artifacts/prd.md#Functional Requirements`

### Open Questions

- Should allowlist management ship with a UI despite the UX spec stating “no configuration in the app”? (Default: minimal UI under Settings/Config.)
- What domain validation policy should be enforced (e.g., allow subdomains only, allow IDN/punycode, allow wildcard prefixes)?
- Should allowlist entries have a stable id separate from the domain string, or is domain-as-id acceptable?

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- create-story workflow (CS 1.3, yolo)
- Tests: `./gradlew test` (api), `npm test` (frontend)

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Implemented allowlist YAML persistence with atomic writes and domain normalization rules.
- Added allowlist API endpoints with RFC 7807 error handling and CRUD tests.
- Built allowlist UI with TanStack Query, minimal layout, and component tests.
- Tests passed: api `./gradlew test`, frontend `npm test`.

### File List

- `/_bmad-output/implementation-artifacts/1-3-manage-allowlist-domains.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `api/src/main/java/com/jobato/api/model/AllowlistEntry.java`
- `api/src/main/java/com/jobato/api/controller/AllowlistController.java`
- `api/src/main/java/com/jobato/api/controller/AllowlistExceptionHandler.java`
- `api/src/main/java/com/jobato/api/dto/AllowlistCreateRequest.java`
- `api/src/main/java/com/jobato/api/dto/AllowlistResponse.java`
- `api/src/main/java/com/jobato/api/dto/AllowlistUpdateRequest.java`
- `api/src/main/java/com/jobato/api/repository/AllowlistRepository.java`
- `api/src/main/java/com/jobato/api/service/AllowlistDuplicateException.java`
- `api/src/main/java/com/jobato/api/service/AllowlistDomainNormalizer.java`
- `api/src/main/java/com/jobato/api/service/AllowlistDomainValidationException.java`
- `api/src/main/java/com/jobato/api/service/AllowlistNotFoundException.java`
- `api/src/main/java/com/jobato/api/service/AllowlistService.java`
- `api/src/main/java/com/jobato/api/service/AllowlistUpdateException.java`
- `api/src/test/java/com/jobato/api/controller/AllowlistControllerTest.java`
- `api/src/test/java/com/jobato/api/repository/AllowlistRepositoryTest.java`
- `api/src/test/java/com/jobato/api/service/AllowlistDomainNormalizerTest.java`
- `config/allowlists.yaml`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/app/App.tsx`
- `frontend/src/app/providers.tsx`
- `frontend/src/app/query-client.ts`
- `frontend/src/app/router.tsx`
- `frontend/src/features/allowlist/api/allowlist-api.ts`
- `frontend/src/features/allowlist/components/AllowlistForm.test.tsx`
- `frontend/src/features/allowlist/components/AllowlistForm.tsx`
- `frontend/src/features/allowlist/components/AllowlistPage.tsx`
- `frontend/src/features/allowlist/components/AllowlistTable.test.tsx`
- `frontend/src/features/allowlist/components/AllowlistTable.tsx`
- `frontend/src/features/allowlist/hooks/use-allowlist.ts`
- `frontend/src/features/allowlist/index.ts`
- `frontend/src/main.tsx`
- `frontend/src/styles/globals.css`
- `frontend/src/test/setup.ts`
- `frontend/tsconfig.app.json`
- `frontend/vite.config.ts`
- `frontend/src/App.tsx` (deleted)
- `frontend/src/App.css` (deleted)
- `frontend/src/index.css` (deleted)

### Change Log

- Implemented allowlist YAML persistence, API CRUD endpoints, and frontend management UI with tests. (2026-02-07)
