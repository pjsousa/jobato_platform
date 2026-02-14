# Story 4.6: Sort by first seen time

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want results sorted by first seen time,
so that the newest items appear first in Today view.

## Acceptance Criteria

1. **Given** results are loaded
   **When** the list is rendered
   **Then** items are sorted by first seen time descending
   **And** the ordering is stable across refreshes

2. **Given** a user switches views
   **When** the list renders
   **Then** the sort order remains consistent
   **And** the active selection is preserved when possible

## Tasks / Subtasks

- [ ] Validate Story 4.1-4.5 baseline prerequisites before coding Story 4.6 (AC: 1, 2)
  - [ ] Confirm Results page/list/detail surface exists and is wired to Today/All Time view state
  - [ ] Confirm Story 4.5 irrelevant visibility toggle behavior exists and is covered by tests
  - [ ] If prerequisite artifacts are missing, deliver them in explicit prerequisite commits before 4.6 logic

- [ ] Define the first-seen contract clearly and keep it camelCase end-to-end (AC: 1, 2)
  - [ ] Treat `createdAt` as the first-seen source for this story unless a dedicated `firstSeenAt` field already exists
  - [ ] If adding `firstSeenAt`, map it from the canonical first-seen source and keep backward compatibility for existing clients
  - [ ] Do not repurpose `lastSeenAt` as first-seen data

- [ ] Implement deterministic backend ordering in results read paths (AC: 1, 2)
  - [ ] Update `ResultRepository` ordering to be deterministic by timestamp and tie-breaker (`... DESC, id DESC`)
  - [ ] Apply the same ordering policy to `/api/results` and `/api/results/by-query` query paths
  - [ ] Preserve duplicate-hiding semantics (`includeHidden`) and any existing filter behavior

- [ ] Implement frontend sort consistency across Today/All Time and refreshes (AC: 1, 2)
  - [ ] Keep one authoritative ordering strategy (prefer API-ordered data; avoid competing in-component sorts)
  - [ ] If client-side sorting is needed, use a stable comparator (`firstSeenAt/createdAt DESC`, then `id DESC`)
  - [ ] Keep sort logic pure and immutable (no in-place array mutation from TanStack Query cache)

- [ ] Preserve active selection whenever the selected item still exists (AC: 2)
  - [ ] Keep selection state keyed by stable result identity (`id`)
  - [ ] On view switch or refresh, retain selection if item remains visible after filter/sort
  - [ ] Fallback to first visible item (or empty-detail state) when selected item is no longer present

- [ ] Keep filtering and sorting responsibilities separated to prevent regressions (AC: 1, 2)
  - [ ] Apply irrelevant visibility filtering and duplicate visibility rules before final list render
  - [ ] Keep Story 4.5 toggle semantics unchanged while introducing Story 4.6 ordering
  - [ ] Ensure count and active-row highlighting reflect the final rendered list order

- [ ] Preserve story boundaries and avoid scope creep (AC: 1, 2)
  - [ ] Do not implement Story 4.7 keyboard interaction matrix in this story
  - [ ] Do not introduce new ranking heuristics based on `relevanceScore` in this story
  - [ ] Do not change feedback label-cycle semantics from Story 4.4/4.5

- [ ] Add targeted tests for ordering stability and selection continuity (AC: 1, 2)
  - [ ] API tests: verify deterministic ordering for equal timestamps via tie-breaker
  - [ ] Frontend tests: Today and All Time render newest-first ordering consistently
  - [ ] Frontend tests: refresh/re-fetch preserves ordering and selected item when still visible
  - [ ] Frontend tests: switching views preserves selected item when possible, otherwise applies fallback behavior

## Dev Notes

### Developer Context

- Story 4.6 introduces explicit first-seen ordering behavior for results list rendering and is tightly coupled to existing selection/visibility behavior from Stories 4.2-4.5.
- Current backend already orders by `created_at DESC` in `ResultRepository`; this story hardens ordering with deterministic tie-breakers and consistent application across result endpoints.
- Current repository still lacks committed `frontend/src/features/results` and `frontend/src/features/feedback` directories; if that remains true, treat Story 4.6 as dependent on prerequisite baseline work.
- Scope focus is deterministic ordering + selection continuity, not new ranking algorithms or keyboard interaction expansion.

### Technical Requirements

- Enforce newest-first ordering using first-seen semantics (`firstSeenAt` if present, otherwise `createdAt`).
- Keep ordering deterministic across refreshes by adding a stable secondary sort (`id DESC`) when timestamps are equal.
- Keep API JSON fields camelCase (`createdAt`, `lastSeenAt`, optional `firstSeenAt`); never introduce snake_case in API payloads.
- Ensure view switching (Today <-> All Time) does not create split-brain state between URL params, local selection state, and rendered order.
- Keep filtering semantics independent from ordering semantics (duplicate visibility and irrelevant visibility must not change behavior).
- Preserve TanStack Query cache immutability; never mutate query data arrays in place while sorting.

### Architecture Compliance

- Frontend implementation belongs under `frontend/src/features/results/*` with route wiring updates in `frontend/src/app/router.tsx` and nav updates in `frontend/src/app/AppLayout.tsx`.
- Server-state loading stays in TanStack Query hooks; no ad-hoc client cache layers.
- API changes remain in controller/service/repository layering under `api/src/main/java/com/jobato/api/*`.
- Keep service boundaries strict: frontend communicates only with API; no direct DB access.
- Preserve RFC 7807 error patterns for any added validation and keep `/api` namespace conventions.

### Library / Framework Requirements

- React Router 7.13.0
  - Keep view mode in URL search params (`useSearchParams`) and use functional updates when toggling a single parameter.
  - Do not mutate `searchParams` outside `setSearchParams`; rely on router-driven URL state for reproducible navigation.

- TanStack Query 5.90.20
  - Use query keys that include view/filter dimensions to avoid cache collisions.
  - Keep derived ordered arrays immutable; if optimistic updates are used, apply immutable `setQueryData` patterns.

- react-window 2.2.6
  - Pass already filtered/sorted data into the virtualized list and keep stable row identity via result `id`.
  - Avoid heavy row computations that can trigger unnecessary re-renders when list order changes.

### File Structure Requirements

- Frontend (create/update as needed)
  - `frontend/src/features/results/api/results-api.ts`
  - `frontend/src/features/results/hooks/use-results.ts`
  - `frontend/src/features/results/components/ResultsPage.tsx`
  - `frontend/src/features/results/components/ResultsPage.css`
  - `frontend/src/features/results/components/ResultsList.tsx`
  - `frontend/src/features/results/components/ResultsList.css`
  - `frontend/src/features/results/components/ResultDetail.tsx`
  - `frontend/src/features/results/components/ResultDetail.css`
  - `frontend/src/features/results/components/ResultsPage.test.tsx`
  - `frontend/src/features/results/components/ResultsList.test.tsx`
  - `frontend/src/features/results/components/ResultDetail.test.tsx`
  - `frontend/src/features/results/index.ts`
  - update `frontend/src/app/router.tsx`
  - update `frontend/src/app/AppLayout.tsx`

- API (update as needed)
  - update `api/src/main/java/com/jobato/api/controller/ResultsController.java`
  - update `api/src/main/java/com/jobato/api/service/ResultService.java`
  - update `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
  - update `api/src/main/java/com/jobato/api/model/ResultItem.java`

- Tests
  - update `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
  - update `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`

### Testing Requirements

- Frontend
  - verify Today list renders newest-first by first-seen field
  - verify All Time list uses the same ordering policy
  - verify ordering remains stable across refetch and refresh cycles
  - verify active selection persists across view switch when selected item remains visible
  - verify fallback selection behavior when selected item is no longer in filtered dataset

- API
  - verify `/api/results` and `/api/results/by-query` return deterministic timestamp-desc ordering
  - verify tie-breaker ordering for identical timestamps is stable and repeatable
  - verify duplicate visibility filters still behave correctly with new ordering rules

### Previous Story Intelligence

- Story 4.5 guardrails to preserve:
  - irrelevant visibility filtering must remain independent from dedupe hidden-item behavior (`isHidden`)
  - URL-driven UI state and selection fallback logic must stay deterministic
  - sorting logic should remain isolated so additional UX stories can evolve independently
- Story 4.5 also identified likely missing committed `results`/`feedback` frontend artifacts; confirm baseline availability before implementing 4.6.

### Git Intelligence Summary

- Most recent commits are docs-heavy and Epic 3 ML work (`ralph 3.7`, docs updates), with no recently committed Epic 4 frontend implementation.
- Existing API results stack (`ResultsController`, `ResultService`, `ResultRepository`) is present and currently orders by `created_at DESC`.
- Treat Story 4.6 frontend work as likely net-new and backend work as targeted, low-surface changes with regression-sensitive tests.

### Latest Tech Information

- React Router guidance confirms `useSearchParams` supports functional updates for mutating one param while preserving others; URL state is the preferred source of truth for view mode.
- TanStack Query guidance confirms cache updates must remain immutable; derived sorting should avoid mutating cached arrays.
- react-window guidance confirms data should be prepared (filtered/sorted) before rendering and rows should use stable identities.

### Project Structure Notes

- Keep `ResultsPage` as orchestration container and keep list/detail components presentational.
- Reuse shared design tokens from `frontend/src/styles/globals.css` for state styling and focus visibility consistency.
- Keep ordering logic centralized (hook or API adapter) to avoid divergent behavior between list and detail contexts.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.6]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/prd.md#Results Review UI]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1: Daily Review (Today list)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: _bmad-output/implementation-artifacts/4-5-toggle-irrelevant-visibility.md]
- [Source: project-context.md#Framework-Specific Rules]
- [Source: project-context.md#Critical Don't-Miss Rules]
- [Source: frontend/src/app/router.tsx]
- [Source: frontend/src/app/AppLayout.tsx]
- [Source: api/src/main/java/com/jobato/api/controller/ResultsController.java]
- [Source: api/src/main/java/com/jobato/api/repository/ResultRepository.java]
- [Source: api/src/main/java/com/jobato/api/model/ResultItem.java]
- [Source: https://reactrouter.com]
- [Source: https://tanstack.com/query/latest]
- [Source: https://github.com/bvaughn/react-window]

### Project Context Reference

- Keep API JSON field names camelCase and aligned with frontend contracts.
- Keep server data in TanStack Query; do not create side caches.
- Keep feature boundaries strict (`features/results` and `features/feedback`) for Epic 4 UX stories.
- Preserve dedupe hidden semantics (`isHidden`) independently from irrelevant visibility and ordering logic.

### Story Completion Status

- Story status set to `ready-for-dev`.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Story input `4-6` resolved to sprint key `4-6-sort-by-first-seen-time` via `sprint-status.yaml`.
- Validation workflow runner not found at `_bmad/core/tasks/validate-workflow.xml`; checklist validation could not be auto-executed.
- Current source tree does not yet contain `frontend/src/features/results` or `frontend/src/features/feedback`.
- Latest technical guidance reviewed via Context7 for React Router (`useSearchParams`), TanStack Query cache immutability, and react-window list preparation guidance.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX specification, project-context, previous Story 4.5 intelligence, git history, and current repository structure.
- Added deterministic ordering guardrails (`timestamp DESC`, tie-breaker by `id DESC`) to prevent refresh jitter.
- Added explicit selection-preservation behavior for Today/All Time view changes.
- Added boundaries to prevent regressions in irrelevant visibility and dedupe-hidden behavior.
- Sprint tracking updated: `4-6-sort-by-first-seen-time` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-6-sort-by-first-seen-time.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
