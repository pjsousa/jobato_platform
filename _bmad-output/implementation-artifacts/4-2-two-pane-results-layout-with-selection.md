# Story 4.2: Two-pane results layout with selection

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want a split layout with a ranked list and a detail panel,
so that I can scan quickly and see context.

## Acceptance Criteria

1. **Given** the Today view loads
   **When** results are present
   **Then** the top-ranked item is selected by default
   **And** its details are shown in the right panel

2. **Given** an item is selected
   **When** I navigate the list
   **Then** the detail panel updates to the selected item
   **And** the list visually highlights the active item

3. **Given** screen width is below 1024px
   **When** the view renders
   **Then** the list stacks above the detail panel
   **And** selection remains persistent across the layout change

## Tasks / Subtasks

- [ ] Validate Story 4.1 baseline dependencies before coding Story 4.2 (AC: 1, 2, 3)
  - [ ] Confirm `frontend/src/features/results/api/results-api.ts` and `frontend/src/features/results/hooks/use-results.ts` exist and are wired
  - [ ] Confirm Results route and navigation entry are present (`/results`)
  - [ ] If Story 4.1 artifacts are missing, implement them first (or in same PR with clearly separated commits)

- [ ] Implement responsive two-pane shell for results page (AC: 1, 3)
  - [ ] Build a split layout at `>=1024px` with list pane on the left and detail pane on the right
  - [ ] Build stacked layout at `<1024px` with list pane above detail pane
  - [ ] Keep layout behavior in component-local CSS using existing global tokens (`--border`, `--surface`, `--muted`, etc.)

- [ ] Implement default selection and detail hydration behavior (AC: 1)
  - [ ] Treat the first item returned for Today as the top-ranked record for default selection
  - [ ] On initial load with data, select first item if no valid selection is active
  - [ ] On empty dataset, clear selection and render the empty-state detail shell

- [ ] Build ranked list interaction with active highlight state (AC: 2)
  - [ ] Render list rows with stable keys (`id`) and explicit selected styling
  - [ ] Update selected result on click and reflect active state immediately in the list
  - [ ] Keep list order as returned by API/query layer (do not introduce client-side re-sorting in this story)

- [ ] Preserve selection through refetches and responsive transitions (AC: 2, 3)
  - [ ] Keep selected ID if it still exists after query/view updates
  - [ ] Fallback to first available item if selected ID disappears
  - [ ] Ensure crossing the `1024px` breakpoint does not reset selected state

- [ ] Add focused test coverage for two-pane selection flow (AC: 1, 2, 3)
  - [ ] Verify Today default selection picks the first item and hydrates detail panel
  - [ ] Verify selecting another list row updates detail content and active styling
  - [ ] Verify stacked layout behavior below `1024px` while preserving selected item
  - [ ] Verify empty/loading states remain correct with split and stacked layouts

## Dev Notes

### Developer Context

- Story 4.2 builds directly on Story 4.1 and should extend the same Results feature surface rather than introducing a parallel page.
- Scope for this story is layout and selection behavior only; do not implement relevance toggle, duplicate count display, first-seen sorting policy changes, or full keyboard interaction requirements from later stories (4.3-4.7).
- Keep implementation incremental: this story establishes the structural shell that later stories refine.

### Technical Requirements

- Selection source of truth should be a page-level `selectedResultId` in the Results feature container.
- Top-ranked selection for AC1 maps to the first result in the Today dataset returned by the query layer.
- Preserve selection on data refresh by checking selected ID against current result IDs before fallback.
- Maintain deterministic rendering behavior:
  - preserve API order from Story 4.1 for now,
  - avoid introducing alternate ranking or sorting logic in this story,
  - reserve first-seen sorting behavior changes for Story 4.6.
- Keep detail pane resilient: render loading, empty, and selected states explicitly.

### Architecture Compliance

- Frontend changes stay under `frontend/src/features/results/*`.
- Route wiring remains in `frontend/src/app/router.tsx`; navigation remains in `frontend/src/app/AppLayout.tsx`.
- Server state remains TanStack Query driven; do not add custom fetch caches.
- Keep API contract camelCase and consume existing `/api/results` responses via typed client code.
- Respect existing service boundaries: no direct DB access from frontend.

### Library / Framework Requirements

- React Router 7.13.0: keep view state URL-driven via `useSearchParams` from Story 4.1.
- TanStack Query 5.90.20:
  - include view mode in query keys (for example `['results', viewMode]`) to prevent cache collisions,
  - use `placeholderData: keepPreviousData` (v5 pattern) to reduce list flicker on key changes.
- react-window 2.2.6: if list size becomes large, keep list component structured to support virtualization without rewriting selection logic.

### File Structure Requirements

- Frontend (create or update as needed)
  - `frontend/src/features/results/components/ResultsPage.tsx`
  - `frontend/src/features/results/components/ResultsPage.css`
  - `frontend/src/features/results/components/ResultsList.tsx`
  - `frontend/src/features/results/components/ResultsList.css`
  - `frontend/src/features/results/components/ResultDetail.tsx`
  - `frontend/src/features/results/components/ResultDetail.css`
  - `frontend/src/features/results/components/ResultsPage.test.tsx`
  - `frontend/src/features/results/index.ts`
  - update `frontend/src/app/router.tsx`
  - update `frontend/src/app/AppLayout.tsx`

### Testing Requirements

- Frontend component tests
  - default Today selection chooses first item
  - active row highlight follows selection changes
  - detail panel updates on selection changes
  - stacked layout path preserves selection under `1024px`
- Integration-style routing test
  - Results route renders with list/detail composition and does not regress Story 4.1 view mode handling
- Regression guardrails
  - no break to loading/empty states from Story 4.1
  - no break to URL-driven view mode state

### Previous Story Intelligence

- Story 4.1 already defined guardrails that must carry forward:
  - use `view=today|all-time` URL state,
  - preserve selected item when possible during data/view changes,
  - keep results data management in TanStack Query hooks.
- Story 4.2 should extend these behaviors with visual layout and explicit selection UX, not replace them.

### Git Intelligence Summary

- Recent commits are primarily Epic 3 backend/ML changes plus guide/documentation updates.
- No recent committed frontend Results feature work was detected; assume Story 4.1 may still be pending implementation and validate baseline before coding Story 4.2.
- Existing test posture indicates JUnit for API and Vitest + Testing Library for frontend; keep that structure.

### Latest Tech Information

- React Router `useSearchParams` remains the recommended way to keep URL query params as UI state; updating search params triggers navigation and keeps back/forward behavior consistent.
- TanStack Query v5 replaced legacy `keepPreviousData` option usage with `placeholderData: keepPreviousData` (or identity function), and exposes `isPlaceholderData` to detect transitional state.
- Query key composition should include view discriminator (`today` vs `all-time`) to avoid cache overlap between datasets.
- react-window supports imperative row scrolling and stable row rendering patterns that can be layered in without changing selection state shape.

### Project Structure Notes

- Maintain a clean seam between container state (`ResultsPage`) and presentational panes (`ResultsList`, `ResultDetail`) to support Stories 4.3-4.7 without major refactors.
- Follow existing visual language in `frontend/src/styles/globals.css` and app shell patterns in `frontend/src/app/AppLayout.css`.
- Keep left pane width in the UX target range (~320-360px) for split layout while allowing detail pane to flex.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1: Daily Review (Today list)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design Direction Decision]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: project-context.md#Framework-Specific Rules]
- [Source: project-context.md#Critical Implementation Rules]
- [Source: _bmad-output/implementation-artifacts/4-1-today-and-all-time-results-views.md]
- [Source: frontend/src/app/router.tsx]
- [Source: frontend/src/app/AppLayout.tsx]
- [Source: frontend/src/features/runs/components/RunStatus.tsx]

### Project Context Reference

- Keep API JSON field usage camelCase end-to-end in frontend types and rendering.
- Keep server data in TanStack Query; avoid ad-hoc local caching layers.
- Keep feature boundaries and naming conventions from architecture and project context.
- Preserve service boundaries; frontend communicates only with API.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Validation task runner not found: `_bmad/core/tasks/validate-workflow.xml`
- Story key resolved from sprint tracking entry: `4-2-two-pane-results-layout-with-selection`
- No existing Story 4.2 file detected; created new story document.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX spec, project-context, Story 4.1 context, and current repository state.
- Added explicit dependency guardrail to avoid implementing Story 4.2 against missing Story 4.1 foundations.
- Added responsive and selection persistence constraints to prevent layout/selection regressions.
- Included current React Router/TanStack Query guidance for URL state and transition-safe query behavior.
- Sprint tracking updated: `4-2-two-pane-results-layout-with-selection` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-2-two-pane-results-layout-with-selection.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
