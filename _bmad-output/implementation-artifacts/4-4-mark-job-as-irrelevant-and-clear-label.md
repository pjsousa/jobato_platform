# Story 4.4: Mark job as irrelevant and clear label

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to mark a job as irrelevant and clear the label if needed,
so that my feedback improves results.

## Acceptance Criteria

1. **Given** a selected job
   **When** I click the title
   **Then** its label cycles Relevant -> Irrelevant -> None
   **And** the list state pill updates accordingly

2. **Given** a label changes
   **When** it is saved
   **Then** the UI updates immediately
   **And** the label is persisted for future runs

3. **Given** a job reappears
   **When** it has a prior label
   **Then** the label can be cleared manually
   **And** the cleared state is saved

## Tasks / Subtasks

- [ ] Validate Story 4.1-4.3 prerequisites before coding Story 4.4 (AC: 1, 2, 3)
  - [ ] Confirm Results baseline exists and is wired (`ResultsPage`, `ResultsList`, `ResultDetail`, routing, URL view state, selection state)
  - [ ] Confirm Story 4.3 key-field rendering baseline exists (or implement as prerequisite in same PR with separated commits)
  - [ ] Confirm API result payload includes stable identity fields for feedback targeting (`id`, `canonicalId`, `normalizedUrl`, `isDuplicate`)

- [ ] Define and implement the manual-feedback persistence contract (AC: 2, 3)
  - [ ] Introduce an explicit tri-state manual label separate from model score: `manualLabel` in `relevant | irrelevant | null`
  - [ ] Keep manual feedback storage independent from `relevanceScore` to avoid corrupting scoring/training semantics
  - [ ] Implement or extend `POST /api/feedback` contract with request validation and RFC 7807 error responses
  - [ ] Return updated feedback state in camelCase (`manualLabel`, `manualLabelUpdatedAt`) for frontend hydration

- [ ] Implement backend label write/read behavior with reappearance handling (AC: 2, 3)
  - [ ] Persist feedback against a stable identity for reappearing jobs (canonical-first with normalized URL fallback)
  - [ ] Ensure clear action persists as null/cleared and remains cleared after refresh/reload
  - [ ] Include `manualLabel` in results payloads returned by `/api/results` and `/api/results/{id}`
  - [ ] Keep duplicate visibility semantics unchanged (hidden duplicates remain hidden unless explicitly requested)

- [ ] Implement title-toggle interaction in the Results detail pane (AC: 1)
  - [ ] Make title action cycle exactly `Relevant -> Irrelevant -> None` on each activation
  - [ ] Update title background state and list state pill immediately on interaction
  - [ ] Show state pills only when label is `relevant` or `irrelevant` (no pill for `none`)
  - [ ] Preserve selected item and view mode state while toggling labels

- [ ] Implement optimistic UI update + rollback-safe persistence in frontend (AC: 1, 2, 3)
  - [ ] Use TanStack Query mutation with `onMutate` cache snapshot + optimistic update
  - [ ] Roll back optimistic label state on mutation failure and surface an actionable error
  - [ ] Invalidate/refetch affected results queries on settled to guarantee eventual consistency
  - [ ] Prevent rapid multi-click race conditions while a toggle mutation is pending

- [ ] Preserve story boundaries and prevent cross-story regressions (AC: 1, 2, 3)
  - [ ] Do not implement Story 4.5 show/hide irrelevant toggle behavior in this story
  - [ ] Do not implement Story 4.6 first-seen sorting changes in this story
  - [ ] Do not implement full Story 4.7 keyboard interaction matrix in this story (only maintain semantic click/activate support)
  - [ ] Keep existing Results ordering/selection behavior from prior stories intact

- [ ] Add targeted tests for label cycle, persistence, and clear semantics (AC: 1, 2, 3)
  - [ ] Frontend tests: title cycle order, immediate pill/title updates, and no-pill behavior for None
  - [ ] Frontend tests: optimistic update rollback and error-state visibility
  - [ ] API tests: set relevant, set irrelevant, clear label, invalid label payload handling
  - [ ] API tests: reappearing job receives previous label via stable identity mapping, then clear persists

## Dev Notes

### Developer Context

- Story 4.4 is the first end-user feedback loop in Epic 4 and directly unlocks FR26/FR27 behavior.
- This story must extend (not replace) the Results review surface from Stories 4.1-4.3.
- Current repository state indicates missing frontend `results`/`feedback` feature folders and no `FeedbackController` yet; treat those as hard prerequisites.
- Scope focus is label cycle + persistence + clear semantics, not broader filtering/sorting/accessibility feature work from later stories.

### Technical Requirements

- Use a dedicated manual feedback state (`manualLabel`) rather than overloading `relevanceScore`.
- Cycle order is strict and deterministic: `relevant -> irrelevant -> null`.
- UI must update instantly on interaction (optimistic), then converge with backend truth after mutation settles.
- Reappearance logic must use stable identity mapping (canonical record preferred; normalized URL fallback when canonical link is unavailable).
- Clearing feedback must fully remove/clear manual label state and persist that clear operation.
- API/DTO fields remain camelCase; no snake_case in JSON payloads.
- Maintain resilience for absent optional fields; no runtime failures when canonical linkage is missing.

### Architecture Compliance

- Frontend changes stay under `frontend/src/features/results/*` and `frontend/src/features/feedback/*`.
- Routing and app-shell nav updates stay in `frontend/src/app/router.tsx` and `frontend/src/app/AppLayout.tsx`.
- Server-state orchestration must stay in TanStack Query hooks; do not add ad-hoc caches.
- API changes follow controller/service/repository layering under `api/src/main/java/com/jobato/api/*`.
- Public API remains under `/api` with RFC 7807 Problem Details for validation/domain errors.
- Respect service boundaries: frontend -> API only; no direct DB access from frontend.

### Library / Framework Requirements

- React Router 7.x: keep view state in URL search params (`useSearchParams`) and avoid split-brain state.
- TanStack Query 5.x: use `useMutation` with `onMutate` snapshot, rollback on `onError`, and `invalidateQueries` on settle.
- React: use semantic interactive controls for title toggle so keyboard activation semantics remain valid for future Story 4.7 expansion.
- Spring Boot 3.5.x: keep endpoint contracts explicit, validate inputs at controller boundary, and return predictable JSON shapes.

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
  - `frontend/src/features/results/components/ResultDetail.test.tsx`
  - `frontend/src/features/results/index.ts`
  - `frontend/src/features/feedback/api/feedback-api.ts`
  - `frontend/src/features/feedback/hooks/use-feedback.ts`
  - `frontend/src/features/feedback/index.ts`
  - update `frontend/src/app/router.tsx`
  - update `frontend/src/app/AppLayout.tsx`

- API (create/update as needed)
  - `api/src/main/java/com/jobato/api/controller/FeedbackController.java`
  - `api/src/main/java/com/jobato/api/service/FeedbackService.java`
  - `api/src/main/java/com/jobato/api/repository/FeedbackRepository.java`
  - `api/src/main/java/com/jobato/api/model/FeedbackLabel.java`
  - `api/src/main/java/com/jobato/api/dto/FeedbackRequest.java`
  - `api/src/main/java/com/jobato/api/dto/FeedbackResponse.java`
  - update `api/src/main/java/com/jobato/api/controller/ResultsController.java`
  - update `api/src/main/java/com/jobato/api/service/ResultService.java`
  - update `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
  - update `api/src/main/java/com/jobato/api/model/ResultItem.java`

- Tests
  - `api/src/test/java/com/jobato/api/controller/FeedbackControllerTest.java`
  - `api/src/test/java/com/jobato/api/service/FeedbackServiceTest.java`
  - update `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
  - update `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`

### Testing Requirements

- Frontend
  - verify title click cycles exactly Relevant -> Irrelevant -> None
  - verify list pill/title background update immediately and stay in sync
  - verify no state pill is rendered for None
  - verify optimistic rollback restores prior label on API failure

- API
  - verify feedback endpoint accepts valid tri-state labels and rejects invalid values
  - verify clear operation persists null state and is returned by read APIs
  - verify results payload includes manual label fields in camelCase
  - verify stable identity lookup applies prior label for reappearing records

### Previous Story Intelligence

- Story 4.3 guardrails to preserve:
  - keep selection state as page-level source of truth
  - preserve active selection across refreshes when possible
  - avoid introducing new sorting behavior in this story
  - retain split/stacked layout behavior established for Results views
- Story 4.3 also noted missing committed Results feature artifacts; treat baseline completion as a prerequisite before finalizing 4.4.

### Git Intelligence Summary

- Recent commits are dominated by docs and Epic 3 retrain work (`Guide update for epic 3`, `ralph 3.7`, `ralph 3.6`); no recent frontend Results feedback implementation landed.
- API pattern from recent commits remains controller + service + test-first coverage in `api/src/test/java`.
- Implement Story 4.4 assuming feedback stack is mostly net-new and must be introduced with clear contracts and tests.

### Latest Tech Information

- React Router `useSearchParams` updates trigger navigation, preserving browser back/forward semantics for URL-driven UI state.
- TanStack Query v5 optimistic mutation best practice is: cancel relevant queries, snapshot cache, `setQueryData` optimistic state, rollback on error, and invalidate on settle.
- For mutation-heavy UI toggles, keep optimistic state local to relevant query keys and avoid global cache mutation side effects.

### Project Structure Notes

- Keep a clean container/presentation boundary (`ResultsPage` owns state orchestration; list/detail components stay focused on rendering + interaction).
- Reuse existing design tokens from `frontend/src/styles/globals.css` for label colors and state pills.
- Keep manual feedback contract forward-compatible with Story 4.5 (irrelevant visibility toggle) by exposing explicit `manualLabel` in results payloads.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/prd.md#Relevance Scoring & Feedback]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 2: Labeling / Feedback Loop (Title toggle)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: _bmad-output/implementation-artifacts/4-3-key-fields-and-duplicate-count-display.md]
- [Source: project-context.md#Framework-Specific Rules]
- [Source: project-context.md#Critical Don't-Miss Rules]
- [Source: frontend/src/app/router.tsx]
- [Source: frontend/src/app/AppLayout.tsx]
- [Source: api/src/main/java/com/jobato/api/controller/ResultsController.java]
- [Source: api/src/main/java/com/jobato/api/model/ResultItem.java]
- [Source: ml/app/pipelines/dedupe.py]
- [Source: ml/app/pipelines/ingestion.py]

### Project Context Reference

- Keep API JSON field names camelCase and aligned with frontend contracts.
- Keep server data in TanStack Query; do not create custom cache layers.
- Keep feature boundaries strict (`features/results` and `features/feedback` for this story).
- Preserve dedupe semantics (canonical linkage + hidden duplicates by default) while adding manual feedback state.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Validation task runner not found: `_bmad/core/tasks/validate-workflow.xml`.
- Story input `4-4` resolved to sprint key `4-4-mark-job-as-irrelevant-and-clear-label` from `sprint-status.yaml`.
- Frontend `results` and `feedback` feature directories were not detected in current source tree during analysis.
- Latest technical guidance reviewed via Context7 for React Router and TanStack Query optimistic update patterns.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX specification, project-context, previous Story 4.3 intelligence, git history, and current repository state.
- Added explicit separation between manual feedback labels and model relevance scoring to prevent data/ML regressions.
- Added stable-identity persistence guidance so reappearing jobs keep label context and support clear semantics.
- Added optimistic-update and rollback guardrails to keep UI responsive without sacrificing consistency.
- Sprint tracking updated: `4-4-mark-job-as-irrelevant-and-clear-label` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-4-mark-job-as-irrelevant-and-clear-label.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
