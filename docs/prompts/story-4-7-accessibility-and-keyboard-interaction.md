# Story 4-7 Plan

## Section 1: Scope and assumptions
- In scope: implement Story 4.7 keyboard and accessibility behavior on the existing Results UX from Stories 4.1-4.6: list keyboard navigation (`ArrowUp`, `ArrowDown`, `Home`, `End`) with list/detail synchronization, deterministic focus visibility, title toggle activation on `Enter`/`Space`, and assistive-technology announcement of label changes.
- Out of scope: implementing missing baseline work from Stories 4.1-4.6 inside this story, changing sorting/filtering semantics from Story 4.5/4.6, adding new backend ranking/ML behavior, or redesigning the Results information architecture.
- Dependencies: Story 4.1-4.6 artifacts must already exist (`frontend/src/features/results/*`, `frontend/src/features/feedback/*`, `/results` route/nav wiring, `manualLabel` persistence contract, and deterministic ordering/selection continuity behaviors).
- Assumptions: use a single deterministic focus model for the listbox (recommended default: container focus with `aria-activedescendant` + `id`-based active row), keep selection state keyed by stable `id`, preserve URL-driven view/filter state as source of truth, and keep TanStack Query as the only server-state cache.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1 (list has focus; arrow keys move selection; detail updates; focus visible) | Add keyboard handlers in Results list container for `ArrowUp`/`ArrowDown` and `Home`/`End`; update selected item in lockstep with active row; keep active row visible in virtualized list via `react-window` list ref scroll API; add explicit ARIA list semantics and persistent focus-indicator styling across selected/relevant/irrelevant states and breakpoints. | Frontend tests: arrow/home/end navigation updates active row and detail pane; focus-visible class/state is present after keyboard interactions; continuity checks across Today/All Time switch, irrelevant toggle, and refetch. | Soft-gate keyboard test/build checks pass and manual keyboard walkthrough confirms deterministic navigation + visible focus at desktop/tablet/mobile breakpoints. |
| AC2 (title focused; Enter/Space cycles label; change announced) | Ensure title interaction is a semantic button (or equivalent button semantics) wired to existing feedback cycle (`relevant -> irrelevant -> none`) and prevent default Space-page-scroll behavior; add/maintain `aria-live` region with concise deterministic announcement text when manual label changes. | Frontend tests: `Enter`/`Space` activates exactly one cycle step per keypress; no duplicate toggles; live-region announcement updates with expected text; regression checks keep list state pill/title state synchronized. | Soft-gate tests plus manual screen-reader/DOM inspection confirm keyboard activation and announcement contract. |

## Section 3: Implementation plan (task list)
1. Validate Story 4.1-4.6 prerequisites before coding Story 4.7; if baseline Results/Feedback artifacts are missing, mark Story 4.7 blocked rather than implementing prerequisite stories in this scope.
2. Define and document the Results list focus model (single owner of DOM focus, active-item identity strategy, and keyboard map) to avoid mixed focus/selection logic across components.
3. Implement list keyboard navigation flow in the Results feature boundary: `ArrowUp`/`ArrowDown` step movement, `Home`/`End` jump behavior, selection/detail synchronization, and scroll-into-view handling for virtualized rows.
4. Implement title keyboard activation semantics in detail view: `Enter`/`Space` toggle cycle exactly once per activation, prevent Space scroll side effects, and keep existing feedback mutation/rollback behavior intact.
5. Add accessibility semantics and visual affordances: list/container labels, active/selected state attributes, persistent high-contrast focus indicators, and non-color-only state communication for labels/pills.
6. Add focused Story 4.7 test coverage and regression assertions for cross-view/filter/refetch continuity; keep Story 4.5 and Story 4.6 behavior boundaries unchanged.
7. Run hard-gate backend dependency checks first; then run frontend soft-gate checks and log any non-blocking UI/a11y follow-ups.

Test plan (unit/integration/API):
- Frontend unit/component: `ResultsList.test.tsx` for arrow/home/end movement, selected-row synchronization, and focus visibility behavior.
- Frontend unit/component: `ResultDetail.test.tsx` (or equivalent) for title keyboard activation (`Enter`/`Space`), single-step tri-state cycle, and live-region announcement text.
- Frontend integration-style: `ResultsPage.test.tsx` for continuity across Today/All Time, show/hide irrelevant, and refetch with selected ID stability.
- API dependency verification (blocking): run existing Results/Feedback controller and service tests to ensure contracts required by Story 4.7 are already stable before frontend keyboard/a11y work proceeds.

Likely files:
- `frontend/src/features/results/components/ResultsPage.tsx`
- `frontend/src/features/results/components/ResultsPage.css`
- `frontend/src/features/results/components/ResultsList.tsx`
- `frontend/src/features/results/components/ResultsList.css`
- `frontend/src/features/results/components/ResultDetail.tsx`
- `frontend/src/features/results/components/ResultDetail.css`
- `frontend/src/features/results/components/ResultsPage.test.tsx`
- `frontend/src/features/results/components/ResultsList.test.tsx`
- `frontend/src/features/results/components/ResultDetail.test.tsx`
- `frontend/src/features/results/hooks/use-results.ts` (only if keyboard continuity logic is centralized in hooks)
- `frontend/src/features/feedback/hooks/use-feedback.ts` (only if keyboard activation path needs shared mutation behavior)
- `frontend/src/features/results/index.ts`
- `frontend/src/app/router.tsx` (only if prerequisite route wiring is still missing and unblocked separately)
- `frontend/src/app/AppLayout.tsx` (only if prerequisite nav wiring is still missing and unblocked separately)

## Section 4: Hard gate (commands + pass criteria)
```bash
# from repository root
test -f api/src/main/java/com/jobato/api/controller/ResultsController.java
test -f api/src/main/java/com/jobato/api/service/ResultService.java
test -f api/src/main/java/com/jobato/api/controller/FeedbackController.java
test -f api/src/main/java/com/jobato/api/service/FeedbackService.java
./api/gradlew -p api test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest" --tests "com.jobato.api.controller.FeedbackControllerTest" --tests "com.jobato.api.service.FeedbackServiceTest"
```
Pass criteria:
- [ ] Required backend dependency files for Results and Feedback contracts exist; missing files are a blocking failure for Story 4.7.
- [ ] Targeted API service/controller tests pass with no regressions (blocking gate).
- [ ] Backend contracts required by Story 4.7 remain stable: camelCase fields, manual-label feedback cycle support, and unchanged dedupe/filter/order semantics from Stories 4.5/4.6.
- [ ] If hard gate fails, Story 4.7 implementation does not proceed until backend/API prerequisites are fixed.

## Section 5: Soft gate (frontend)
Checks:
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultsList.test.tsx`
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultDetail.test.tsx`
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultsPage.test.tsx`
- [ ] `npm --prefix frontend run build`
- [ ] Manual check (keyboard only): with list focus, `ArrowUp`/`ArrowDown` move one row, `Home`/`End` jump first/last visible row, and detail panel stays synchronized.
- [ ] Manual check (keyboard + toggle): with title focused, `Enter` and `Space` each apply exactly one label cycle step and Space does not scroll page.
- [ ] Manual check (assistive semantics): list and rows expose expected role/state attributes; live region announces label updates with deterministic message text.
- [ ] Manual check (responsive focus): focus indicators remain visible and high-contrast in split (`>=1024px`), stacked (`768-1023px`), and fallback (`<768px`) layouts.
Follow-ups if failing:
- Log failing frontend checks with exact repro sequence (URL params, viewport width, focused element, key sequence, expected vs actual behavior).
- Create targeted non-blocking follow-up tasks for visual/accessibility polish while preserving hard-gate backend status and story boundaries.

## Section 6: Risks and rollback
- Risks: Story 4.1-4.6 baselines are currently absent on this branch (primary blocker); virtualization can desync active row and scroll position if identity/focus ownership is inconsistent; keyboard handlers can conflict with native page scroll if default prevention is incomplete; live-region announcements can become noisy or duplicated if mutation lifecycle emits multiple updates.
- Rollback steps: revert Story 4.7 frontend keyboard/a11y changes in `frontend/src/features/results/components/*` (and any related hook changes), restore prior click-only interaction behavior, rerun hard-gate API tests and frontend soft-gate checks to confirm baseline restoration.

## Section 7: Blockers/questions (if any)
1) Current branch does not contain prerequisite Story 4.1-4.6 implementation artifacts (`frontend/src/features/results/*`, `frontend/src/features/feedback/*`, and Feedback API stack are missing). Should Story 4.7 remain blocked until those stories are merged first? (Recommended: Yes - treat this as a hard blocker and keep Story 4.7 strictly scoped to keyboard/a11y once prerequisites exist.)
