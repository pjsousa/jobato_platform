# Story 4-3 Plan

## Section 1: Scope and assumptions
- In scope: implement Story 4.3 presentation behavior on top of the existing Results surface from Stories 4.1/4.2: list rows show `title`, `company`, `snippet`, `source`, `postedDate`; duplicate badge renders only when `duplicateCount > 0`; detail pane shows duplicate count, canonical-context messaging, and a safe external source link.
- Out of scope: implementing missing Story 4.1/4.2 foundation artifacts, Story 4.4-4.7 behaviors (label toggling, irrelevant visibility toggle, first-seen sorting controls, full keyboard interaction), ML/dedupe algorithm changes, and schema migrations.
- Dependencies: Story 4.1 route/data-layer baseline (`/results`, `results-api`, `use-results`) and Story 4.2 layout/selection baseline (`ResultsPage`, `ResultsList`, `ResultDetail`, `selectedResultId` behavior) must already exist; Epic 3 dedupe API fields (`canonicalId`, `isDuplicate`, `duplicateCount`) must remain available.
- Assumptions: `company` and `postedDate` are not guaranteed from API yet, so deterministic frontend fallbacks are used (`company <- domain`, `postedDate <- createdAt`); source link prefers `finalUrl` then falls back to `rawUrl`; hidden duplicates remain hidden by default but duplicate-context messaging handles both canonical and duplicate records defensively.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1 (key fields in list + duplicate count visibility) | Extend results row render contract to include title prominence, company/snippet/source/posted metadata, and conditional duplicate badge (`duplicateCount > 0` only). Add deterministic formatting/fallback helpers for missing company/date/source inputs without changing list ordering or selection behavior. | Frontend component tests: list row renders all required fields; duplicate badge appears only for positive counts; no regression in active-row selection/highlight behavior from Story 4.2. | Soft-gate frontend test/build checks and manual verification at `/results` (desktop + mobile widths) confirm visible fields and conditional duplicate badge behavior. |
| AC2 (detail duplicate context + source link) | Update `ResultDetail` to show canonical linkage context and duplicate count, including canonical/duplicate role messaging based on `isDuplicate` and `canonicalId`. Surface source link with `target="_blank"` and `rel="noopener noreferrer"`, using `finalUrl` fallback to `rawUrl`. | Frontend component tests: canonical context text + duplicate count for canonical records; duplicate-link context when duplicate surfaced; source link URL and safe attributes are asserted. API tests only if contract changes are introduced. | Hard-gate API contract tests pass (blocking) and soft-gate detail rendering checks pass/logged (non-blocking), with safe-link attributes verified in tests/manual check. |

## Section 3: Implementation plan (task list)
1. Validate prerequisite baseline from Stories 4.1/4.2 before coding Story 4.3; if Results feature artifacts are missing, stop and track as blocker instead of implementing prior stories inside Story 4.3.
2. Extend the frontend results DTO/mapping in `results-api` (or adjacent helper) to expose a stable display contract for this story: `title`, `company`, `snippet`, `source`, `postedDate`, `duplicateCount`, `canonicalId`, `isDuplicate`, `finalUrl`/`rawUrl`.
3. Add deterministic display helpers for fallback formatting: domain-to-company/source label, safe posted-date formatting from `createdAt`, and resilient null/empty handling for snippet/date/url values.
4. Update `ResultsList` rendering to show the required key fields and conditional duplicate count chip while preserving API order, selected-row behavior, and existing responsive two-pane/stacked composition.
5. Update `ResultDetail` rendering to surface duplicate count, canonical-context messaging, and source link behavior (safe external-link attributes and URL fallback path).
6. Add/adjust CSS for metadata density and badge contrast using existing global tokens, ensuring list/detail readability and no regression in Story 4.2 layout behavior.
7. Add focused frontend tests for AC1/AC2 plus regression checks for selection/highlight continuity; add API tests only if backend response contract is changed for this story.

Test plan (unit/integration/API):
- Frontend unit/component: `ResultsPage.test.tsx` (or split list/detail tests) for key-field rendering, duplicate-badge conditional behavior, detail canonical-context messaging, and safe source-link attributes.
- Frontend regression: preserve Story 4.2 selection behavior (default first item, click-to-select, active highlight) while adding metadata fields.
- API unit (dependency verification): run existing `ResultsControllerTest` and `ResultServiceTest` to ensure dedupe/canonical fields remain stable in camelCase.
- API extension coverage (conditional): if `company`/`postedDate` are added server-side, extend controller/service tests to assert backward compatibility and camelCase payloads.

Likely files:
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
- `api/src/main/java/com/jobato/api/controller/ResultsController.java` (only if API contract is expanded)
- `api/src/main/java/com/jobato/api/service/ResultService.java` (only if API contract is expanded)
- `api/src/main/java/com/jobato/api/repository/ResultRepository.java` (only if API contract is expanded)
- `api/src/main/java/com/jobato/api/model/ResultItem.java` (only if API contract is expanded)
- `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java` (only if API contract is expanded)
- `api/src/test/java/com/jobato/api/service/ResultServiceTest.java` (only if API contract is expanded)

## Section 4: Hard gate (commands + pass criteria)
```bash
# from repository root
./api/gradlew -p api test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"
```
Pass criteria:
- [ ] Command exits successfully (blocking gate) with no API/service test failures.
- [ ] Results API contract remains camelCase and still exposes dedupe/context fields used by Story 4.3 (`duplicateCount`, `canonicalId`, `isDuplicate`, `finalUrl`, `rawUrl`, `domain`, `createdAt`).
- [ ] No backend/API/ML regressions are introduced; if backend is untouched, this gate still passes as dependency verification.
- [ ] If API fields are expanded for this story, backward compatibility is preserved for existing consumers and reflected in updated tests.

## Section 5: Soft gate (frontend)
Checks:
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultsPage.test.tsx`
- [ ] `npm --prefix frontend run build`
- [ ] Manual check (desktop `>=1024px`): list rows show title/company/snippet/source/posted date; duplicate badge appears only when count is positive.
- [ ] Manual check (mobile `<1024px`): stacked layout remains intact and selected item persists while metadata rendering remains readable.
- [ ] Manual check: detail pane shows canonical-context copy + duplicate count and renders source link with `target="_blank"` + `rel="noopener noreferrer"`.
- [ ] Manual check: adding key fields does not change ordering or break active-row selection behavior.
Follow-ups if failing:
- Log failing frontend checks with repro steps (URL/view, viewport width, selected item, expected vs actual output).
- Create targeted non-blocking follow-up tasks for UI polish/accessibility refinements while keeping hard-gate backend status explicit.

## Section 6: Risks and rollback
- Risks: Story 4.1/4.2 baseline may be missing on the target branch (blocking this story); fallback formatting may produce low-quality company/date labels for sparse data; canonical-context text can become misleading if duplicate visibility behavior changes later; badge/link styling may regress contrast or row density.
- Rollback steps: revert `frontend/src/features/results/components/*` and related DTO/helper changes for Story 4.3; restore pre-4.3 list/detail rendering contract; rerun API hard gate and frontend soft-gate checks to confirm baseline behavior is restored.

## Section 7: Blockers/questions (if any)
1) Story 4.1/4.2 prerequisite artifacts are currently absent on this branch (`frontend/src/features/results/*` and `/results` route/nav wiring are not present). Should Story 4.3 remain blocked until Stories 4.1 and 4.2 are merged? (Recommended: Yes - treat both as strict preconditions and keep Story 4.3 scoped to key-fields/duplicate-context only.)
