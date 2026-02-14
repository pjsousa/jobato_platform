# Story 4.7: Accessibility and keyboard interaction

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want full keyboard navigation and accessible UI,
so that I can use the app efficiently.

## Acceptance Criteria

1. **Given** the list has focus
   **When** I use arrow keys
   **Then** selection moves and the detail panel updates
   **And** focus remains visible at all times

2. **Given** the title is focused
   **When** I press Enter or Space
   **Then** the label cycles
   **And** the change is announced to assistive tech

## Tasks / Subtasks

- [ ] Validate Story 4.1-4.6 prerequisites before coding Story 4.7 (AC: 1, 2)
  - [ ] Confirm Results view baseline exists (Today/All Time tabs, split or stacked layout, list/detail selection flow)
  - [ ] Confirm Story 4.4/4.5 feedback baseline exists (`manualLabel` tri-state and persistence path)
  - [ ] Confirm Story 4.6 ordering and selection continuity behavior is in place
  - [ ] If prerequisite artifacts are missing, implement them in explicit prerequisite commits before 4.7 keyboard/a11y work

- [ ] Define keyboard interaction and focus model for Results list (AC: 1)
  - [ ] Use a deterministic list focus model (roving focus or listbox + `aria-activedescendant`) and document which element owns DOM focus
  - [ ] Support `ArrowDown` and `ArrowUp` to move active selection one row at a time
  - [ ] Support `Home` and `End` to jump to first/last visible row for long lists
  - [ ] Keep selected row and detail panel strictly synchronized on every keyboard navigation action

- [ ] Implement keyboard navigation with virtualization-safe behavior (AC: 1)
  - [ ] Ensure keyboard-selected item is brought into view when using virtualized rendering (`react-window` list imperative scroll API)
  - [ ] Keep stable item identity (`id`) so selection survives rerenders and refetches
  - [ ] Prevent page scroll side effects while list navigation keys are handled
  - [ ] Maintain behavior consistency in Today and All Time views

- [ ] Implement title keyboard toggle with assistive technology announcement (AC: 2)
  - [ ] Make title control keyboard focusable with explicit action semantics (`button` preferred)
  - [ ] Handle `Enter` and `Space` to cycle `Relevant -> Irrelevant -> None` exactly once per activation
  - [ ] Prevent default Space key page scroll when toggle is activated from keyboard
  - [ ] Announce label change via an accessible live region (`aria-live`) with concise, deterministic message text

- [ ] Enforce visible focus and WCAG-aligned interaction affordances (AC: 1, 2)
  - [ ] Keep a persistent, high-contrast focus indicator for list rows and title toggle in all states (default, selected, relevant, irrelevant)
  - [ ] Ensure keyboard focus remains perceivable in split layout (>=1024px), stacked layout (768-1023px), and fallback (<768px)
  - [ ] Keep hit targets >=44px and preserve explicit labels for interactive controls
  - [ ] Do not rely on color alone for state communication

- [ ] Preserve existing behavior boundaries and prevent regressions (AC: 1, 2)
  - [ ] Do not change Story 4.6 ordering policy (`firstSeen/createdAt DESC`, tie-breaker stability)
  - [ ] Do not change Story 4.5 irrelevant visibility semantics (`showIrrelevant` remains independent from dedupe-hidden records)
  - [ ] Do not repurpose dedupe flags (`isHidden`, `isDuplicate`) for keyboard focus or label state
  - [ ] Keep server-state authority in TanStack Query and avoid ad-hoc client caches

- [ ] Add targeted tests for keyboard and accessibility contracts (AC: 1, 2)
  - [ ] Frontend tests: `ArrowUp`/`ArrowDown` move selection and update detail panel
  - [ ] Frontend tests: `Home`/`End` jump correctly and keep focus visible
  - [ ] Frontend tests: `Enter`/`Space` on title cycles labels and triggers live-region announcement
  - [ ] Frontend tests: selection + focus continuity across Today/All Time switch, toggle filtering, and refetch
  - [ ] API tests only if contract changes are required for feedback payloads (camelCase fields preserved)

## Dev Notes

### Developer Context

- Story 4.7 is the accessibility and keyboard completion slice for Epic 4 Results UX and must preserve all behavior introduced by Stories 4.1-4.6.
- Current repository still does not contain committed `frontend/src/features/results` or `frontend/src/features/feedback` artifacts; treat keyboard/a11y work as dependent on those prerequisites.
- Existing API Results stack is present (`ResultsController`, `ResultService`, `ResultRepository`, `ResultItem`) and already exposes dedupe/scoring fields in camelCase.
- Scope focus is keyboard navigation + assistive tech semantics, not new ranking, filtering, or backend architecture changes.

### Technical Requirements

- Keyboard navigation must update active selection and detail pane in lockstep.
- Focus and selection must be deterministic and remain stable across rerenders/refetch.
- Title toggle keyboard activation must follow exact tri-state sequence: `relevant -> irrelevant -> none`.
- Accessibility semantics must include a labeled list container and row-level selection state (`aria-selected` or equivalent consistent convention).
- Announcements for feedback label changes must be concise and deterministic for screen readers.
- URL-driven view/filter state must remain the source of truth where already established (do not introduce parallel local URL state).

### Architecture Compliance

- Frontend implementation belongs under `frontend/src/features/results/*` and `frontend/src/features/feedback/*`.
- Route registration and app navigation updates belong in `frontend/src/app/router.tsx` and `frontend/src/app/AppLayout.tsx`.
- Server-state orchestration remains in TanStack Query hooks; no side caches or in-place mutation of query data.
- API changes (only if unavoidable for missing feedback contracts) must follow controller/service/repository layering in `api/src/main/java/com/jobato/api/*`.
- Public contracts remain under `/api` with camelCase JSON and RFC 7807 error behavior.

### Library / Framework Requirements

- React Router 7.13.0
  - Use `useSearchParams` functional updates when changing one query param while preserving others.
  - Remember `setSearchParams` callback updates are not React state-queue semantics; avoid multi-call same-tick assumptions.

- TanStack Query 5.90.20
  - Keep derived sorting/filtering/focus lists immutable.
  - Use query keys that include all dimensions affecting results visibility and list content.
  - If optimistic updates are used for label changes, keep snapshot/rollback/invalidate pattern.

- react-window 2.2.6
  - Keep row rendering lightweight and pass pre-processed visible data into list renderer.
  - Use list ref imperative scrolling (`scrollToRow`) for keyboard-driven navigation visibility.
  - Keep stable row identity by result `id`.

- WAI-ARIA Authoring Practices (Listbox pattern)
  - Support keyboard interactions: `ArrowUp`, `ArrowDown`, and strongly recommended `Home`/`End` for long lists.
  - Keep focus and selection semantics explicit and predictable.
  - For virtualized/dynamic lists, ensure positional semantics remain coherent for assistive tech (`aria-posinset` / `aria-setsize` when needed).

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
  - `frontend/src/features/feedback/api/feedback-api.ts` (update if already present)
  - `frontend/src/features/feedback/hooks/use-feedback.ts` (update if already present)
  - update `frontend/src/app/router.tsx`
  - update `frontend/src/app/AppLayout.tsx`

- API (only if prerequisite feedback/result contract gaps are discovered)
  - update `api/src/main/java/com/jobato/api/controller/ResultsController.java`
  - update `api/src/main/java/com/jobato/api/service/ResultService.java`
  - update `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
  - update `api/src/main/java/com/jobato/api/model/ResultItem.java`
  - update `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
  - update `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`

### Testing Requirements

- Frontend
  - verify list keyboard navigation updates selected row and detail panel
  - verify `Home`/`End` behavior and focus visibility in long lists
  - verify title keyboard activation (`Enter`/`Space`) cycles labels and announces changes
  - verify focus/selection continuity across view switch, irrelevant toggle, and refetch
  - verify ARIA attributes and interactive labels are present on list container, rows, and title toggle

- API (if touched)
  - verify response contracts remain camelCase
  - verify dedupe visibility and existing result retrieval semantics remain unchanged

### Previous Story Intelligence

- Story 4.6 guardrails to preserve:
  - deterministic ordering policy (`createdAt` / first-seen desc with stable tie-break)
  - selection continuity across Today/All Time changes
  - strict separation between filtering semantics and ordering semantics
- Story 4.6 flagged likely missing committed results/feedback artifacts; validate baseline availability before implementing Story 4.7.

### Git Intelligence Summary

- Last five commits are mostly docs and Epic 3 ML work (`bump huide`, `Guide update for epic 3`, `ralph 3.7`, `ralph 3.6`).
- No recent commits establish Epic 4 frontend Results/Feedback implementation baseline.
- Existing API results stack is present and test-covered, making regression-safe incremental changes possible once frontend baseline exists.

### Latest Tech Information

- React Router docs: `setSearchParams` callback mutates and returns `URLSearchParams`; use functional updates to preserve unrelated params.
- React Router docs: callback updates trigger navigation but do not provide React setState queueing behavior.
- TanStack Query docs: cache updates must be immutable (`setQueryData` updater should return new objects/arrays, never mutate old cache values).
- react-window docs: imperative list ref scrolling (`scrollToRow`) is appropriate for keyboard shortcuts/navigation where active item must remain visible.
- W3C APG listbox guidance: explicit keyboard model (`Arrow` keys, recommended `Home/End`), clear distinction between focus and selection, and explicit role/state semantics.

### Project Structure Notes

- Keep `ResultsPage` as orchestration container and keep list/detail components presentational.
- Centralize keyboard behavior in one results feature boundary to avoid divergent key handling across components.
- Reuse shared visual tokens in `frontend/src/styles/globals.css` for focus and label state styling consistency.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.7]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/prd.md#Results Review UI]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1: Daily Review (Today list)]
- [Source: _bmad-output/implementation-artifacts/4-6-sort-by-first-seen-time.md]
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
- [Source: https://www.w3.org/WAI/ARIA/apg/patterns/listbox/]

### Project Context Reference

- Keep API JSON field names camelCase and aligned with frontend contracts.
- Keep server data in TanStack Query and avoid side caches.
- Keep feature boundaries strict (`features/results`, `features/feedback`) for Epic 4 UX implementation.
- Preserve dedupe semantics (`isHidden`) independently from label state and keyboard focus behavior.

### Story Completion Status

- Story status set to `ready-for-dev`.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Story input `4-7` resolved to sprint key `4-7-accessibility-and-keyboard-interaction` via `sprint-status.yaml`.
- Loaded planning artifacts (`epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`), project context, and previous Story 4.6 context.
- Validation workflow runner not found at `_bmad/core/tasks/validate-workflow.xml`; checklist validation could not be auto-executed.
- Latest technical guidance reviewed via Context7 (`react-router`, `tanstack/query`, `react-window`) and W3C APG listbox pattern.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX spec, project-context rules, previous Story 4.6 intelligence, git history, and current repository state.
- Added explicit keyboard interaction model guardrails (Arrow/Home/End) with virtualization-safe visibility handling.
- Added title-toggle keyboard and assistive-technology announcement requirements with regression boundaries.
- Added explicit prerequisite checks because results/feedback feature artifacts are not currently committed.
- Sprint tracking updated: `4-7-accessibility-and-keyboard-interaction` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-7-accessibility-and-keyboard-interaction.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
