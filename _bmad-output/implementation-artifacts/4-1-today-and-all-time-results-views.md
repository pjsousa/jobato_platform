# Story 4.1: Today and All Time results views

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to switch between Today and All Time views,
so that I can focus on new results or review history.

## Acceptance Criteria

1. **Given** results exist
   **When** I select Today
   **Then** I see only results new since the last run
   **And** the list is filtered accordingly

2. **Given** results exist
   **When** I select All Time
   **Then** I see the full history of results
   **And** the list reflects all stored items

3. **Given** the view changes
   **When** data is loading
   **Then** a clear loading state is shown
   **And** the prior selection is preserved when possible

## Tasks / Subtasks

- [ ] Implement Today/All Time results query contract in API (AC: 1, 2)
  - [ ] Extend `GET /api/results` to accept `view=today|all-time` (default `today`) with existing `includeHidden` support
  - [ ] Keep `runId` query support temporarily for backward compatibility while moving frontend to `view`
  - [ ] For `today`, resolve the latest run from run summary metadata and return only that run's results
  - [ ] For `all-time`, return results across all run IDs available in the active database

- [ ] Implement results feature data layer in frontend (AC: 1, 2)
  - [ ] Create `frontend/src/features/results/api/results-api.ts` with typed contracts and RFC 7807-style error handling
  - [ ] Create `frontend/src/features/results/hooks/use-results.ts` with query keys scoped by view mode
  - [ ] Use TanStack Query with placeholder previous data on view switches to avoid list flicker

- [ ] Add Today/All Time UI entry point and routing (AC: 1, 2, 3)
  - [ ] Add Results route to `frontend/src/app/router.tsx` and navigation entry in `frontend/src/app/AppLayout.tsx`
  - [ ] Create `frontend/src/features/results/components/ResultsPage.tsx` with Today/All Time tabs
  - [ ] Persist active view in URL search params (`view=today|all-time`) using React Router

- [ ] Preserve selected item across view changes where possible (AC: 3)
  - [ ] Track selected result ID in state for the current page
  - [ ] On view change + data refresh, keep selected ID if present in the new dataset
  - [ ] If selected ID is absent, fall back to first available item (or null for empty state)

- [ ] Implement explicit loading and empty states for results view switching (AC: 3)
  - [ ] Show a visible loading indicator while the selected view is fetching
  - [ ] Keep previous content visible during fetch and label it as updating
  - [ ] Provide clear empty-state messaging when a selected view has no results

- [ ] Add targeted tests for behavior and regressions (AC: 1, 2, 3)
  - [ ] API controller/service tests for `today` vs `all-time` filtering and query param handling
  - [ ] Frontend tests for tab switching, loading indicators, URL-param-driven view state, and selection retention
  - [ ] Ensure response/DTO casing remains camelCase and existing `/api/results?runId=...` behavior is not broken

## Dev Notes

### Developer Context

- This story starts Epic 4 and establishes the review surface that Stories 4.2-4.7 will build on.
- Existing backend already exposes `GET /api/results` and run summaries (`GET /api/reports/runs/latest`), so this story should extend current flows rather than create parallel endpoints.
- Scope boundary: implement view switching + loading/selection continuity only; do not implement labeling toggle, duplicate count rendering, advanced sorting controls, or accessibility refinements from later stories.

### Technical Requirements

- Today view must be derived from the latest run context (latest available run metadata) and return only that run's items.
- All Time view must include all available results in active storage; ordering should be deterministic and stable (`createdAt` descending unless stronger first-seen semantics are introduced later).
- Keep API JSON fields camelCase and preserve existing response compatibility for current consumers.
- Selection continuity rule:
  - Keep selected item if it still exists after view/data change.
  - Otherwise select first available item.
  - Otherwise clear selection.
- Loading states must be explicit and user-visible during view transitions.

### Architecture Compliance

- Frontend remains under feature boundaries: `frontend/src/features/results/*`.
- Router ownership stays in `frontend/src/app/router.tsx`; no custom routing abstraction.
- Server state must use TanStack Query (no ad-hoc caches or duplicated fetch state machines).
- API stays under `/api/results` with REST + JSON conventions and RFC 7807 error handling patterns.
- Respect existing SQLite active-db model through API repository/service layers; do not bypass service boundaries from frontend.

### Library / Framework Requirements

- React Router 7.13.0 for route + search-param state (`useSearchParams` for view mode).
- TanStack Query 5.90.20 for results retrieval and transition behavior.
- Spring Boot 3.5.10.RELEASE + Java 17 for controller/service/repository updates.
- Testing stack unchanged:
  - Frontend: Vitest + Testing Library
  - API: JUnit + Spring test patterns already used in `api/src/test/java`

### File Structure Requirements

- Frontend
  - `frontend/src/features/results/api/results-api.ts`
  - `frontend/src/features/results/hooks/use-results.ts`
  - `frontend/src/features/results/components/ResultsPage.tsx`
  - `frontend/src/features/results/components/ResultsPage.test.tsx`
  - `frontend/src/features/results/index.ts`
  - Update `frontend/src/app/router.tsx`
  - Update `frontend/src/app/AppLayout.tsx`

- API
  - Update `api/src/main/java/com/jobato/api/controller/ResultsController.java`
  - Update `api/src/main/java/com/jobato/api/service/ResultService.java`
  - Update `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
  - Add/update tests:
    - `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
    - `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`

### Testing Requirements

- API
  - Verify `view=today` returns only latest-run records.
  - Verify `view=all-time` returns full result history from active DB.
  - Verify backward compatibility for `runId` query behavior.
  - Verify includeHidden behavior is consistent for both views.

- Frontend
  - Verify default view is Today.
  - Verify switching tabs updates URL search params and query key.
  - Verify loading state is shown during view transitions.
  - Verify selected item is preserved when still present, and falls back correctly when absent.

### Latest Tech Information

- React Router guidance supports using URL search params for UI state like list/detail view modes; this avoids split-brain state between local component state and URL.
- TanStack Query v5 favors `placeholderData` identity behavior (or `keepPreviousData` helper) for smooth transitions when query keys change across views.
- Query key discipline matters here: include view mode in query keys (for example `['results', viewMode]`) to avoid cache collisions between Today and All Time datasets.

### Project Structure Notes

- Keep this story intentionally thin on layout complexity; Story 4.2 will formalize two-pane layout and default selection behavior in detail.
- Reuse existing run summary/reporting signals rather than introducing a new latest-run tracking mechanism.
- Maintain current visual language and CSS token usage from `frontend/src/styles/globals.css` and existing page shells.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/prd.md#Results Review UI]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Boundaries]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1: Daily Review (Today list)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: project-context.md#Framework-Specific Rules]
- [Source: project-context.md#Critical Don't-Miss Rules]
- [Source: api/src/main/java/com/jobato/api/controller/ResultsController.java]
- [Source: frontend/src/app/router.tsx]

### Project Context Reference

- Use camelCase JSON in API responses.
- Keep frontend server data in TanStack Query; no bespoke caches.
- Keep feature boundaries and naming conventions from architecture/project-context.
- Preserve service boundaries; frontend never reads SQLite directly.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Validation task file not found: `_bmad/core/tasks/validate-workflow.xml`
- No previous story in Epic 4; previous-story intelligence intentionally skipped for Story 4.1.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX spec, project context, and current codebase state.
- Added explicit guardrails for API compatibility and frontend selection continuity to reduce implementation regressions.
- Included latest React Router and TanStack Query guidance relevant to view transitions and loading behavior.
- Sprint tracking updated: `epic-4` -> `in-progress`, `4-1-today-and-all-time-results-views` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-1-today-and-all-time-results-views.md
