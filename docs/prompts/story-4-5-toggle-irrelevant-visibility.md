# Story 4-5 Plan

## Section 1: Scope and assumptions
- In scope: add URL-driven `showIrrelevant` toggle behavior on the Results surface so `manualLabel === 'irrelevant'` rows are hidden by default, shown when enabled, visually de-emphasized when shown, and reflected in visible list counts and selection fallback behavior.
- Out of scope: implementing Story 4.6 sorting, Story 4.7 keyboard matrix work, changing duplicate-hiding semantics (`includeHidden`/`isHidden`), and creating Story 4.1-4.4 foundations inside this story.
- Dependencies: direct dependency on Story 4.4 contracts (`manualLabel` tri-state in results payload and `POST /api/feedback` persistence); functional dependency on Story 4.1-4.3 Results feature baseline (`frontend/src/features/results/*`, `/results` route/nav, list/detail selection behavior).
- Assumptions: irrelevant filtering is a frontend visibility rule derived from existing result payloads (not a new backend filter endpoint); list header total for this story is based on post-filter visible items.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1 (toggle off hides irrelevant + filtered count) | Add `showIrrelevant` URL param contract (default `false`), derive `visibleResults = results.filter(r => r.manualLabel !== 'irrelevant')` when off, keep dedupe-hidden behavior independent, and update selected-item fallback when current selection is removed by filter. | `ResultsPage.test.tsx`: default/off state excludes irrelevant rows; count reflects visible list; selected item falls back deterministically if hidden by toggle change. | Hard gate confirms backend `manualLabel` contract exists; soft gate test run confirms off-state filtering/count/selection behavior. |
| AC2 (toggle on shows irrelevant with de-emphasis + label visible) | Wire toggle control to URL state using functional `setSearchParams`, include irrelevant rows when on, apply de-emphasized row/detail styles while keeping label pills visible, and preserve Today/All Time context/query state. | `ResultsList.test.tsx` + `ResultDetail.test.tsx`: on-state includes irrelevant rows, applies de-emphasis class, and keeps visible label rendering. `ResultsPage.test.tsx`: URL/back-forward behavior for `showIrrelevant`. | Soft gate checks pass for targeted tests plus manual browser validation of URL persistence and visual treatment. |

## Section 3: Implementation plan (task list)
1. Run prerequisite audit for Story 4.4 and Results baseline: verify `manualLabel` is returned by results APIs, `POST /api/feedback` exists, and Results feature/route artifacts from Stories 4.1-4.3 are present; if missing, stop as blocked.
2. Define toggle state contract in Results container: parse `showIrrelevant` from search params with default `false`, update via functional `setSearchParams`, and preserve existing params (`view`, `runId`, `includeHidden`) and browser history semantics.
3. Implement deterministic visibility filtering in Results state composition: apply irrelevant filter after API data hydration and independent of dedupe-hidden behavior; keep row identity by `id` and avoid introducing Story 4.6 sorting logic.
4. Update selection/count logic to operate on filtered dataset: maintain selected ID when still visible, otherwise fallback to next visible/first/null; render totals from current visible results and optionally helper text for hidden irrelevant count.
5. Add toggle UI and de-emphasis styling: place control in Results page controls area; style irrelevant rows/detail with reduced emphasis while preserving label pill visibility and WCAG AA contrast/focus states.
6. Add frontend test coverage for AC1/AC2 plus regression checks for URL param persistence and back/forward navigation semantics.
7. Run hard gate (blocking) then soft gate (non-blocking); document any soft-gate failures with reproducible steps.

Test plan (unit/integration/API):
- Frontend unit/component: `ResultsPage.test.tsx` for default toggle state, filtered counts, selection fallback, and URL state transitions.
- Frontend component: `ResultsList.test.tsx` and `ResultDetail.test.tsx` for de-emphasized styling + visible label behavior when `showIrrelevant=true`.
- Frontend routing integration-style: verify `showIrrelevant` coexists with `view=today|all-time` and supports browser back/forward.
- API contract validation (dependency gate): verify Story 4.4 tests and Results API tests cover `manualLabel` availability and no dedupe semantic regression.

Likely files:
- `frontend/src/features/results/components/ResultsPage.tsx`
- `frontend/src/features/results/components/ResultsPage.css`
- `frontend/src/features/results/components/ResultsList.tsx`
- `frontend/src/features/results/components/ResultsList.css`
- `frontend/src/features/results/components/ResultDetail.tsx`
- `frontend/src/features/results/components/ResultDetail.css`
- `frontend/src/features/results/hooks/use-results.ts`
- `frontend/src/features/results/api/results-api.ts`
- `frontend/src/features/results/components/ResultsPage.test.tsx`
- `frontend/src/features/results/components/ResultsList.test.tsx`
- `frontend/src/features/results/components/ResultDetail.test.tsx`
- `frontend/src/features/feedback/api/feedback-api.ts` (only if feedback contract typings need alignment)
- `frontend/src/features/feedback/hooks/use-feedback.ts` (only if feedback hydration/mutation contract needs alignment)

## Section 4: Hard gate (commands + pass criteria)
```bash
# from repository root
rg -n "manualLabel|manualLabelUpdatedAt" api/src/main/java/com/jobato/api/controller/ResultsController.java api/src/main/java/com/jobato/api/model/ResultItem.java api/src/main/java/com/jobato/api/repository/ResultRepository.java
rg -n "@RequestMapping\(\"/api/feedback\"\)|@PostMapping" api/src/main/java/com/jobato/api/controller/FeedbackController.java
./api/gradlew -p api test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest" --tests "com.jobato.api.controller.FeedbackControllerTest" --tests "com.jobato.api.service.FeedbackServiceTest"
```
Pass criteria:
- [ ] Contract check shows `manualLabel` (tri-state) is mapped through Results API layers and exposed in camelCase response payloads.
- [ ] Feedback write path exists at `/api/feedback` and related backend tests pass.
- [ ] Results/feedback API tests pass without regressing duplicate-hide semantics (`includeHidden` and `isHidden` behavior unchanged).
- [ ] Any failure in these commands is a blocking failure for Story 4.5 implementation/merge.

## Section 5: Soft gate (frontend)
Checks:
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultsPage.test.tsx src/features/results/components/ResultsList.test.tsx src/features/results/components/ResultDetail.test.tsx`
- [ ] `npm --prefix frontend run build`
- [ ] Manual check: `/results?view=today` defaults to hidden irrelevant items when `showIrrelevant` is absent.
- [ ] Manual check: toggling on (`showIrrelevant=true`) shows irrelevant rows with de-emphasis and visible labels.
- [ ] Manual check: toggling off after selecting an irrelevant row applies selection fallback safely (next visible/first/null).
- [ ] Manual check: browser back/forward restores previous `showIrrelevant` state without losing Today/All Time context.
Follow-ups if failing:
- Log failing checks with URL, viewport, action sequence, expected vs actual behavior, and console/test output.
- Create focused follow-up tasks for UI regressions while keeping hard-gate dependency status explicit.

## Section 6: Risks and rollback
- Risks: Story 4.4 dependency may be absent in target branch (no `manualLabel`/feedback endpoint), causing a hard block; filter logic could accidentally couple to dedupe hidden semantics; selection may thrash if fallback is not ID-driven; URL param updates can clobber other search params if not functional/merged.
- Rollback steps: revert Story 4.5-specific Results UI/filter changes in `frontend/src/features/results/components/*` and related hook/api typing updates; restore prior Results behavior; rerun hard-gate backend commands and baseline frontend soft-gate checks to confirm pre-story behavior.

## Section 7: Blockers/questions (if any)
1) Current repository snapshot lacks Story 4.4 implementation artifacts (`manualLabel` in API payloads, `FeedbackController`, and `frontend/src/features/results/*` baseline files). Should Story 4.5 remain blocked until Story 4.4 (and 4.1-4.3 baseline) is merged? (Recommended: Yes - enforce dependency completion as a hard prerequisite and keep Story 4.5 scoped strictly to visibility toggle behavior.)
