# Story 4.5: Toggle irrelevant visibility

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to hide or show irrelevant items,
so that I can focus on the most relevant results.

## Acceptance Criteria

1. **Given** the toggle is off
   **When** a job is labeled irrelevant
   **Then** it is hidden from the list
   **And** the total count reflects the filtered view

2. **Given** the toggle is on
   **When** irrelevant items exist
   **Then** they are shown with de-emphasized styling
   **And** their labels remain visible

## Tasks / Subtasks

- [ ] Validate Story 4.4 feedback prerequisites before coding Story 4.5 (AC: 1, 2)
  - [ ] Confirm result payload includes `manualLabel` as tri-state (`relevant | irrelevant | null`)
  - [ ] Confirm label persistence path exists (`POST /api/feedback` and read hydration in results endpoints)
  - [ ] If Story 4.4 artifacts are missing, complete/merge them first or include them as explicit prerequisite commits

- [ ] Define irrelevant-visibility state contract and URL behavior (AC: 1, 2)
  - [ ] Add URL search param `showIrrelevant` with default `false`
  - [ ] Preserve existing search params when toggling via functional `setSearchParams` updates
  - [ ] Keep browser back/forward semantics and deep-link reproducibility for toggle state

- [ ] Implement filtering semantics without breaking duplicate-hiding rules (AC: 1, 2)
  - [ ] When `showIrrelevant=false`, exclude items where `manualLabel === 'irrelevant'`
  - [ ] When `showIrrelevant=true`, include irrelevant-labeled items and keep label pills visible
  - [ ] Keep duplicate semantics independent: preserve existing `includeHidden` behavior for dedupe-hidden records

- [ ] Implement toggle control and list/detail behavior in Results UX (AC: 1, 2)
  - [ ] Place a clear show/hide irrelevant control in the Results page controls area
  - [ ] Apply filter immediately on toggle state change without losing Today/All Time context
  - [ ] If current selection becomes filtered out when toggle turns off, select next visible item (or safe empty detail state)

- [ ] Implement de-emphasized styling rules for visible irrelevant items (AC: 2)
  - [ ] Apply reduced-emphasis visual treatment to irrelevant rows and related detail title treatment
  - [ ] Keep irrelevant label visible when shown
  - [ ] Preserve WCAG AA contrast and focus visibility for all interactive states

- [ ] Ensure counts reflect filtered visibility state (AC: 1)
  - [ ] Render list totals from currently visible dataset after irrelevant filtering
  - [ ] Keep count updates synchronized with query data, view mode, and toggle state
  - [ ] Optionally show hidden-item helper text without introducing extra filtering controls

- [ ] Preserve scope boundaries and prevent regressions (AC: 1, 2)
  - [ ] Do not implement Story 4.6 first-seen sorting changes in this story
  - [ ] Do not implement Story 4.7 full keyboard interaction matrix in this story
  - [ ] Do not repurpose `isHidden` duplicate semantics as irrelevant-label state

- [ ] Add targeted tests for toggle/filter behavior and integration safety (AC: 1, 2)
  - [ ] Frontend tests: toggle off hides irrelevant items and count reflects filtered list
  - [ ] Frontend tests: toggle on shows irrelevant items with de-emphasized styling and visible label pills
  - [ ] Frontend tests: selection fallback behavior when selected item becomes hidden by toggle off
  - [ ] Frontend tests: URL param persistence and back/forward behavior for show/hide state
  - [ ] API tests (if backend filtering/count contracts change): verify camelCase fields and dedupe-filter coexistence

## Dev Notes

### Developer Context

- Story 4.5 extends Story 4.4 feedback behavior by adding visibility filtering for irrelevant-labeled jobs; it does not redefine label persistence.
- Current repository state does not yet contain `frontend/src/features/results` or `frontend/src/features/feedback`; treat Story 4.1-4.4 baselines as prerequisites for implementation.
- Existing backend duplicate visibility (`includeHidden`) is already in use for dedupe behavior and must remain separate from irrelevant-label filtering.
- Scope focus is show/hide irrelevant behavior, filtered counts, and visual treatment consistency across Today/All Time views.

### Technical Requirements

- Introduce explicit UI visibility state `showIrrelevant` (`false` by default).
- Use `manualLabel` as the source for irrelevant filtering; do not infer irrelevant from `relevanceScore`.
- Keep toggle filtering deterministic and idempotent across refresh, route navigation, and query refetch.
- Preserve selected-item continuity when dataset changes due to filtering.
- Keep API payloads camelCase and resilient when optional fields are absent (`manualLabel` may be null).
- Ensure count shown in the list header reflects post-filter visible items.

### Architecture Compliance

- Frontend work belongs under `frontend/src/features/results/*` and `frontend/src/features/feedback/*`.
- Route wiring and app navigation updates belong in `frontend/src/app/router.tsx` and `frontend/src/app/AppLayout.tsx`.
- Server data orchestration must stay in TanStack Query hooks; no ad-hoc client-side caches.
- API changes (if needed) follow controller/service/repository layering in `api/src/main/java/com/jobato/api/*`.
- Public contracts remain under `/api` with camelCase JSON and RFC 7807 error behavior for invalid input.

### Library / Framework Requirements

- React Router 7.13.0
  - Use `useSearchParams` for `showIrrelevant` URL state.
  - Use functional updates when changing one param so existing params are not clobbered.
  - Expect `setSearchParams` to navigate and preserve browser history behavior.

- TanStack Query 5.90.20
  - Scope query keys by result view + run identity + visibility flags to avoid cache overlap.
  - Keep optimistic feedback mutation pattern from Story 4.4 (`onMutate` snapshot, rollback on `onError`, invalidate on `onSettled`).
  - Avoid separate local caches that can drift from server-state truth.

- react-window 2.2.6
  - Keep row rendering lightweight for virtualization compatibility.
  - Filter dataset before passing to list renderer and keep stable row identity by result `id`.

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
  - `frontend/src/features/feedback/api/feedback-api.ts` (update if needed)
  - `frontend/src/features/feedback/hooks/use-feedback.ts` (update if needed)
  - update `frontend/src/app/router.tsx`
  - update `frontend/src/app/AppLayout.tsx`

- API (if backend visibility/count contract updates are required)
  - update `api/src/main/java/com/jobato/api/controller/ResultsController.java`
  - update `api/src/main/java/com/jobato/api/service/ResultService.java`
  - update `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
  - update `api/src/main/java/com/jobato/api/model/ResultItem.java`
  - update `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
  - update `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`

### Testing Requirements

- Frontend
  - verify toggle default hides irrelevant items when `showIrrelevant` is absent/false
  - verify toggle on shows irrelevant items with visible labels and de-emphasized styling
  - verify visible count reflects filtered list after each toggle change
  - verify selected-item fallback when filtered list removes current selection
  - verify URL search param drives state and supports browser back/forward

- API (if changed)
  - verify result/filter endpoints preserve camelCase response fields
  - verify irrelevant filtering does not alter duplicate hiding semantics
  - verify count endpoints (if modified) return values aligned with filtered visibility

### Previous Story Intelligence

- Story 4.4 established key guardrails to preserve:
  - manual feedback state must stay separate from `relevanceScore`
  - title-toggle interaction uses deterministic tri-state cycle and optimistic updates
  - selection continuity and existing Results view behavior must not regress
- Story 4.4 also flagged likely missing committed `results`/`feedback` feature artifacts; validate baseline availability before implementing 4.5.

### Git Intelligence Summary

- Last five commits are mostly docs and Epic 3 ML retrain work (`bump huide`, `Guide update for epic 3`, `ralph 3.7`, `ralph 3.6`), with no recent committed Epic 4 UI implementation.
- Treat Story 4.5 implementation as likely net-new on frontend and potentially dependent on unmerged Story 4.4 baseline.
- Existing backend pattern remains controller/service/repository with JUnit tests under `api/src/test/java`.

### Latest Tech Information

- React Router docs confirm `useSearchParams` updates trigger navigation; URL param state is appropriate for persistent UI filter controls.
- React Router functional `setSearchParams` updates are preferred when mutating a single key while preserving other params.
- TanStack Query v5 optimistic update best practice remains: cancel relevant queries, snapshot previous cache, optimistic update, rollback on error, invalidate on settle.
- react-window guidance remains to keep row renderers minimal and list data pre-processed (filtered/sorted) before rendering.

### Project Structure Notes

- Keep container state orchestration in `ResultsPage`; keep list/detail components presentational.
- Reuse shared tokens from `frontend/src/styles/globals.css` for de-emphasis and state-pill styling consistency.
- Keep visibility toggle logic isolated from sorting logic so Story 4.6 can be implemented independently.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.5]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/prd.md#Results Review UI]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1: Daily Review (Today list)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 2: Labeling / Feedback Loop (Title toggle)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: _bmad-output/implementation-artifacts/4-4-mark-job-as-irrelevant-and-clear-label.md]
- [Source: project-context.md#Framework-Specific Rules]
- [Source: project-context.md#Critical Don't-Miss Rules]
- [Source: frontend/src/app/router.tsx]
- [Source: frontend/src/app/AppLayout.tsx]
- [Source: api/src/main/java/com/jobato/api/controller/ResultsController.java]
- [Source: api/src/main/java/com/jobato/api/model/ResultItem.java]

### Project Context Reference

- Keep API JSON field names camelCase and aligned with frontend contracts.
- Keep server data in TanStack Query; do not introduce side caches.
- Keep feature boundaries strict (`features/results` and `features/feedback`) for this story.
- Preserve dedupe semantics (`isHidden` for duplicates) independently from irrelevant visibility filtering.

### Story Completion Status

- Story status set to `ready-for-dev`.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Story input `4-5` resolved to sprint key `4-5-toggle-irrelevant-visibility` via `sprint-status.yaml`.
- Validation workflow runner not found at `_bmad/core/tasks/validate-workflow.xml`; checklist validation could not be auto-executed.
- Current source tree does not yet contain `frontend/src/features/results` or `frontend/src/features/feedback`.
- Latest technical guidance reviewed via Context7 for React Router (`useSearchParams`), TanStack Query optimistic updates, and react-window list rendering guidance.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX specification, project-context, previous Story 4.4 intelligence, git history, and current repository structure.
- Added explicit guardrails to keep irrelevant filtering separate from duplicate-hiding semantics.
- Added URL-driven state requirements to prevent toggle-state drift across refresh and navigation.
- Added selection-fallback and filtered-count requirements to prevent list/detail inconsistency regressions.
- Sprint tracking updated: `4-5-toggle-irrelevant-visibility` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-5-toggle-irrelevant-visibility.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
