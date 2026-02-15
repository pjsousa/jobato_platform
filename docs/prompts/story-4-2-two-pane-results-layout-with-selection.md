# Story 4-2 Plan

## Section 1: Scope and assumptions
- In scope: implement Story 4.2 UI behavior on the existing Results surface from Story 4.1: two-pane layout at `>=1024px`, stacked layout at `<1024px`, default selection of the first Today result, list/detail synchronization on selection, active-row visual highlight, and selection persistence across refetches and breakpoint changes.
- Out of scope: Story 4.1 foundation work (creating the Results feature/API hook/route/nav if missing), backend/API/ML feature changes, and Story 4.3-4.7 behaviors (key fields polish, duplicate display enhancements, label toggling, irrelevant visibility toggle, first-seen sort policy changes, keyboard-accessibility refinements).
- Dependencies: Story 4.1 contracts and artifacts must already exist (`GET /api/results?view=today|all-time`, `frontend/src/features/results/api/results-api.ts`, `frontend/src/features/results/hooks/use-results.ts`, `/results` route in `frontend/src/app/router.tsx`, nav entry in `frontend/src/app/AppLayout.tsx`).
- Assumptions: selection source of truth is page-level `selectedResultId`; top-ranked for this story means first item returned by API/query layer for Today; preserve API order (no client-side resorting); fallback behavior is keep selected ID if present else first item else `null`.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1 (default selection + detail pane) | Update `ResultsPage` container to auto-select first Today item when no valid selection exists; render selected item in `ResultDetail`; keep explicit loading and empty-detail states. | `ResultsPage.test.tsx`: first-item default selection, detail hydration, empty dataset clears selection. | Soft-gate test run passes for `ResultsPage.test.tsx`; manual check at `/results?view=today` shows first row selected and detail pane populated. |
| AC2 (list navigation updates detail + highlight) | Implement/extend `ResultsList` with row click handling, `id`-based stable keys, selected row styling, and callback to update `selectedResultId`; ensure detail panel updates immediately from selected record. | `ResultsPage.test.tsx` plus `ResultsList.test.tsx` (if split): click on another row updates detail content and active style. | Soft-gate tests pass and verify no client-side reordering (render order matches mocked API order). |
| AC3 (responsive stack + selection persistence) | Add responsive layout styles (`>=1024px` split, `<1024px` stacked) in results CSS; keep selection state in container so resizing/reflow does not reset selected item; preserve/fallback selection across query refreshes. | `ResultsPage.test.tsx`: resize breakpoint scenario keeps selected item; refetch scenario preserves ID or falls back first/null deterministically. | Soft-gate tests and manual viewport checks (desktop + tablet/mobile widths) confirm layout switch without selection reset. |

## Section 3: Implementation plan (task list)
1. Validate Story 4.1 prerequisites before coding Story 4.2; if baseline Results feature artifacts are missing, stop and hand off as blocker instead of implementing Story 4.1 inside this story.
2. Refactor/extend `ResultsPage` to own `selectedResultId` and deterministic selection lifecycle (initial load, refetch retain/fallback, empty state clear).
3. Implement `ResultsList` interaction contract: row rendering by `id`, selected visual state, click-to-select behavior, and API-order rendering.
4. Implement `ResultDetail` state rendering for loading, empty/no selection, and selected item content without introducing Story 4.3+ field requirements.
5. Implement responsive two-pane shell styles in results CSS with `1024px` breakpoint and persistent composition between list and detail panes.
6. Keep URL-driven view handling from Story 4.1 intact (`view=today|all-time`) and ensure selection logic responds safely to view/data changes.
7. Add focused frontend tests for AC1-AC3 behaviors and guard against regressions in loading/empty states.

Test plan (unit/integration/API):
- Frontend unit/component: `ResultsPage.test.tsx` for default selection, selection change highlight, detail updates, empty/loading behavior, and breakpoint persistence.
- Frontend component (optional split): `ResultsList.test.tsx` for active-row styling and click selection callback behavior.
- Frontend routing integration-style: verify `/results` still honors URL `view` state while rendering list/detail composition.
- API dependency verification (no new API implementation in Story 4.2): run Results API tests from Story 4.1 as a blocking precondition.

Likely files:
- `frontend/src/features/results/components/ResultsPage.tsx`
- `frontend/src/features/results/components/ResultsPage.css`
- `frontend/src/features/results/components/ResultsList.tsx`
- `frontend/src/features/results/components/ResultsList.css`
- `frontend/src/features/results/components/ResultDetail.tsx`
- `frontend/src/features/results/components/ResultDetail.css`
- `frontend/src/features/results/components/ResultsPage.test.tsx`
- `frontend/src/features/results/index.ts`
- `frontend/src/app/router.tsx` (only if Story 4.1 route is missing and this story is formally unblocked to include baseline wiring)
- `frontend/src/app/AppLayout.tsx` (only if Story 4.1 nav entry is missing and this story is formally unblocked to include baseline wiring)

## Section 4: Hard gate (commands + pass criteria)
```bash
# from repository root
./api/gradlew -p api test --tests "com.jobato.api.service.ResultServiceTest" --tests "com.jobato.api.controller.ResultsControllerTest"
```
Pass criteria:
- [ ] Results API tests pass with Story 4.1 contract behavior available (`view=today|all-time`, includeHidden consistency, legacy `runId` compatibility).
- [ ] No backend/API/ML regressions are introduced by Story 4.2 work (Story 4.2 should be frontend-only).
- [ ] If this hard gate fails, Story 4.2 implementation is blocked until backend dependency is fixed.

## Section 5: Soft gate (frontend)
Checks:
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultsPage.test.tsx`
- [ ] `npm --prefix frontend run build`
- [ ] Manual check at `>=1024px`: `/results` shows split list/detail layout with active list highlight.
- [ ] Manual check at `<1024px`: list stacks above detail and selected item remains unchanged when crossing breakpoint.
- [ ] Manual check: Today view default selects first returned item and detail pane hydrates correctly.
- [ ] Manual check: selecting a different row updates detail immediately and preserves API order.
Follow-ups if failing:
- Log failing frontend checks with repro steps (viewport width, URL state, user action sequence, expected vs actual behavior).
- Create targeted follow-up tasks for non-blocking UI regressions while keeping hard-gate backend status explicit.

## Section 6: Risks and rollback
- Risks: Story 4.1 baseline may be absent on target branch; selection may reset on refetch if state derives from object identity instead of ID; breakpoint logic may drift if CSS/media query and tests use inconsistent thresholds; loading/placeholder states can briefly show stale detail if fallback ordering is non-deterministic.
- Rollback steps: revert results layout/selection changes in `frontend/src/features/results/components/*`; restore prior Results page behavior from Story 4.1 baseline; rerun frontend soft-gate checks and API hard-gate tests to confirm baseline restored.

## Section 7: Blockers/questions (if any)
1) Story 4.1 baseline artifacts appear missing in the current branch (no `frontend/src/features/results/*` and no `/results` route/nav wiring detected). Should Story 4.2 remain blocked until Story 4.1 is merged? (Recommended: Yes - treat Story 4.1 completion as a strict precondition and keep Story 4.2 scoped to layout/selection only.)
