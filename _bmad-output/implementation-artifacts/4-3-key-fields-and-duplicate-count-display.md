# Story 4.3: Key fields and duplicate count display

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to see key job fields and duplicate counts,
so that I can judge relevance quickly.

## Acceptance Criteria

1. **Given** a result item
   **When** it is displayed in the list
   **Then** it shows title, company, snippet, source, and posted date
   **And** duplicate count is shown when available

2. **Given** a canonical item
   **When** it is displayed in detail
   **Then** it shows the duplicate count and canonical linkage
   **And** the detail view surfaces the source link

## Tasks / Subtasks

- [ ] Validate Story 4.1 and 4.2 prerequisites before coding Story 4.3 (AC: 1, 2)
  - [ ] Confirm Results feature baseline exists (`ResultsPage`, `ResultsList`, `ResultDetail`, routing, and URL view state)
  - [ ] Confirm selection behavior from Story 4.2 exists (default first-item selection + active highlight + responsive persistence)
  - [ ] If Story 4.1/4.2 artifacts are missing, implement them first (or in same PR with clearly separated commits)

- [ ] Define and enforce key-field display contract for results list/detail (AC: 1, 2)
  - [ ] Ensure frontend result DTO includes fields needed for this story: `title`, `company`, `snippet`, `source`, `postedDate`, `duplicateCount`, `canonicalId`, `isDuplicate`, `finalUrl`
  - [ ] Keep API payloads camelCase end-to-end
  - [ ] If `company`/`postedDate` are not provided by backend yet, implement deterministic fallback mapping in frontend:
    - [ ] company fallback from `domain` (human-readable label)
    - [ ] postedDate fallback from `createdAt` (formatted display)
  - [ ] Keep fallback behavior explicit and non-breaking (no runtime errors on null/empty values)

- [ ] Implement key-field rendering in the ranked list UI (AC: 1)
  - [ ] Render title prominently in each row
  - [ ] Render company, snippet preview, source label, and posted date as secondary metadata
  - [ ] Render duplicate count badge/chip only when `duplicateCount > 0`
  - [ ] Preserve existing list ordering and selection behavior (no additional sorting in this story)

- [ ] Implement canonical-context details and source link behavior in detail pane (AC: 2)
  - [ ] Show duplicate count in detail view for canonical records (`isDuplicate === false`)
  - [ ] Show canonical linkage indicator text in detail:
    - [ ] canonical item: indicate it is canonical and how many duplicates are linked
    - [ ] duplicate item (if surfaced): indicate canonical link via `canonicalId`/`canonicalRecord` when available
  - [ ] Surface source link using `finalUrl` (fallback `rawUrl` if required)
  - [ ] Ensure external-link safety (`target="_blank"` + `rel="noopener noreferrer"`)

- [ ] Keep layout/performance/accessibility guardrails intact while adding new fields (AC: 1, 2)
  - [ ] Do not regress two-pane/stacked layout behavior from Story 4.2
  - [ ] Keep row rendering lightweight and ready for `react-window` virtualization patterns
  - [ ] Keep interactive list rows keyboard-focusable with visible focus states (full keyboard interaction enhancements remain Story 4.7)
  - [ ] Preserve WCAG AA-friendly contrast for duplicate/count badges and metadata text

- [ ] Add targeted test coverage for key-fields + duplicate-count behavior (AC: 1, 2)
  - [ ] Frontend tests: list row shows title/company/snippet/source/posted date
  - [ ] Frontend tests: duplicate badge renders only when count is available and greater than zero
  - [ ] Frontend tests: detail pane shows duplicate count + canonical context text for canonical records
  - [ ] Frontend tests: source link is rendered with expected URL and safe link attributes
  - [ ] API tests (if backend contract updated): response mapping includes expected camelCase fields and remains backward compatible

## Dev Notes

### Developer Context

- Story 4.3 extends the Epic 4 review surface created by Stories 4.1 and 4.2; it should enrich result presentation, not replace the flow.
- Primary goal is decision speed: show enough metadata in list/detail for quick relevance judgment.
- Scope boundary: do not implement label toggle (Story 4.4), irrelevant visibility toggle (Story 4.5), first-seen sort controls (Story 4.6), or full keyboard interaction behavior (Story 4.7).

### Technical Requirements

- Required key fields in list item:
  - title: `title`
  - company: backend-provided when available; otherwise deterministic fallback from `domain`
  - snippet: `snippet` (trimmed for list readability)
  - source: human-readable source from `domain`
  - posted date: backend-provided when available; otherwise formatted from `createdAt`
- Duplicate display rule:
  - show duplicate count only when count is greater than zero
  - hidden duplicates remain hidden by default; canonical row still shows linked duplicate count
- Detail-pane requirements:
  - include duplicate-count summary for canonical record
  - include canonical linkage messaging to clarify record role
  - include source URL link for direct navigation to original posting
- Defensive rendering:
  - gracefully handle missing `snippet`, `domain`, `finalUrl`, and timestamp fields
  - avoid throwing on malformed dates; provide readable fallback text

### Architecture Compliance

- Keep frontend work in `frontend/src/features/results/*`.
- Keep route wiring in `frontend/src/app/router.tsx` and navigation entry in `frontend/src/app/AppLayout.tsx`.
- Keep server-state access in TanStack Query hooks; do not introduce ad-hoc caches.
- Keep API JSON response casing camelCase in controller responses.
- Preserve service boundaries: frontend talks to API only; no direct SQLite access from frontend.

### Library / Framework Requirements

- React Router (7.x): use URL search params (`useSearchParams`) as view-state source of truth so URL changes remain navigable via browser back/forward.
- TanStack Query (5.x):
  - keep query keys scoped by view/filter state to avoid cache collisions
  - use `placeholderData: keepPreviousData` for transition stability when switching result views
  - use `isPlaceholderData` where needed to distinguish transitional data
- react-window (2.2.6): keep row rendering structured for virtualization compatibility and stable item identity (`id`) without rewriting selection logic.

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
  - `frontend/src/features/results/index.ts`
  - update `frontend/src/app/router.tsx`
  - update `frontend/src/app/AppLayout.tsx`

- API (only if key-field contract additions are required)
  - update `api/src/main/java/com/jobato/api/controller/ResultsController.java`
  - update `api/src/main/java/com/jobato/api/service/ResultService.java`
  - update `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
  - update `api/src/main/java/com/jobato/api/model/ResultItem.java`
  - update `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
  - update `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`

### Testing Requirements

- Frontend
  - verify list rows render key fields for each result item
  - verify duplicate badge visibility rules (`duplicateCount > 0`)
  - verify detail pane canonical context + duplicate count behavior
  - verify source link rendering and attributes
  - verify no regression in Story 4.2 selection/highlight behavior

- API (if changed)
  - verify response mapping includes all required key fields in camelCase
  - verify no regression for existing dedupe/scoring fields
  - verify backward compatibility for consumers already using existing result fields

### Previous Story Intelligence

- Story 4.2 guardrails to preserve:
  - keep selection state as page-level source of truth
  - preserve selected ID when possible through data/view changes
  - do not introduce new sorting behavior in this story
  - retain split/stacked responsive behavior across `1024px` breakpoint
- Story 4.2 also flagged potential missing Story 4.1 implementation artifacts; validate baseline before implementing 4.3 UI enrichment.

### Git Intelligence Summary

- Recent commits are mostly documentation and Epic 3 backend/ML work (`Guide update for epic 3`, `ralph 3.7`, `ralph 3.6`).
- No recent committed frontend Results feature implementation was detected; assume Story 4.1/4.2 may still need completion before 4.3.
- Existing test posture remains Vitest + Testing Library (frontend) and JUnit (API); keep that structure.

### Latest Tech Information

- React Router `useSearchParams` updates perform navigation and preserve browser history semantics for URL-driven UI state.
- TanStack Query v5 migration guidance favors `placeholderData` with `keepPreviousData` (or identity function) and `isPlaceholderData` over deprecated `keepPreviousData` option flags.
- Query-key scoping by view/filter parameters remains critical to prevent cache overlap between Today and All Time datasets.
- react-window list patterns emphasize lightweight row renderers with stable row identity and optional imperative scrolling support for selection workflows.

### Project Structure Notes

- Keep clean separation between container state (`ResultsPage`) and presentational list/detail components to avoid refactors in Stories 4.4-4.7.
- Reuse existing global styling tokens in `frontend/src/styles/globals.css` for visual consistency.
- Keep metadata density balanced for scan speed; avoid visual clutter in list rows.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Daily Review and Feedback UX]
- [Source: _bmad-output/planning-artifacts/prd.md#Results Review UI]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Naming Conventions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Strategy]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design & Accessibility]
- [Source: _bmad-output/implementation-artifacts/4-2-two-pane-results-layout-with-selection.md]
- [Source: project-context.md#Framework-Specific Rules]
- [Source: project-context.md#Critical Don't-Miss Rules]
- [Source: api/src/main/java/com/jobato/api/controller/ResultsController.java]
- [Source: api/src/main/java/com/jobato/api/model/ResultItem.java]
- [Source: ml/app/pipelines/dedupe.py]

### Project Context Reference

- Keep API JSON field names camelCase and aligned with frontend contracts.
- Keep server data access in TanStack Query (no custom cache layers).
- Keep feature boundaries strict (`features/results` for results UX changes).
- Preserve dedupe semantics (canonical linkage + hidden duplicates by default) from existing backend behavior.

## Dev Agent Record

### Agent Model Used

openai/gpt-5.3-codex

### Debug Log References

- Validation task runner not found: `_bmad/core/tasks/validate-workflow.xml`.
- Story input `4-3` resolved to sprint key `4-3-key-fields-and-duplicate-count-display` from `sprint-status.yaml`.
- Results feature implementation files not detected in current frontend tree; prerequisite guardrails added.
- Latest technical guidance reviewed via Context7 for React Router, TanStack Query, and react-window.

### Completion Notes List

- Story drafted from epics, PRD, architecture, UX specification, project-context, previous Story 4.2 intelligence, git history, and current repository state.
- Added concrete key-field contract and fallback strategy to prevent ambiguous implementation when company/posted date are not yet explicit backend fields.
- Added canonical/duplicate rendering guardrails to prevent regressions in dedupe semantics.
- Added explicit scope boundaries to avoid accidental implementation of Stories 4.4-4.7 concerns.
- Sprint tracking updated: `4-3-key-fields-and-duplicate-count-display` -> `ready-for-dev`.

### File List

- _bmad-output/implementation-artifacts/4-3-key-fields-and-duplicate-count-display.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
