# Story 4-1 Plan

## Section 1: Scope and assumptions
- In scope: add `view=today|all-time` support to `GET /api/results` (default `today`), keep `includeHidden` behavior, keep legacy `runId` query support, add Results page route/tab UI, persist view in URL search params, preserve selected item across view changes when possible, and show explicit loading/empty states.
- Out of scope: Story 4.2+ behaviors (two-pane layout, key fields/duplicate rendering refinements, label toggle, irrelevant visibility toggle, first-seen sorting policy change, accessibility keyboard refinements), ML pipeline/model logic, and any schema migrations.
- Dependencies: Story 2.3 data in `run_items` (results persisted by run), Story 2.6 latest run metadata in `run_summaries` (`/api/reports/runs/latest` flow), existing Results API/service/repository stack in API, and React Router + TanStack Query frontend patterns.
- Assumptions: `today` maps to latest `runId` from `run_summaries` ordered by `trigger_time DESC`; if `runId` is provided it takes precedence over `view` for backward compatibility; if no latest summary exists for `today`, return `200` with an empty list.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1 (Today view) | Extend `/api/results` to accept `view`; resolve latest run from run summary metadata; return only that run's results; preserve `includeHidden` filtering. | API service/controller tests for `view=today`, latest-run resolution, and `includeHidden` behavior. | Targeted API tests pass for latest-run-only filtering and compatibility assertions. |
| AC2 (All Time view) | Add repository/service path to fetch across all `run_id` values in active DB, deterministic order (`created_at DESC`, tie-breaker `id DESC` if needed). | API service/controller tests for `view=all-time` returning cross-run history with deterministic ordering. | Targeted API tests pass for all-time dataset and ordering checks. |
| AC3 (Loading + selection continuity) | Build Results page with Today/All Time tabs backed by URL search params; TanStack Query keys include view; keep previous data visible during fetch; preserve selected ID if still present else fallback first/null; explicit loading and empty state text. | Frontend component tests for default view, tab switch URL sync, loading/updating indicators, and selection retention/fallback behavior. | Soft-gate frontend checks logged; non-blocking failures tracked as follow-ups. |

## Section 3: Implementation plan (task list)
1. Update API controller contract in `ResultsController` to support `view=today|all-time` while keeping legacy `runId` handling and existing response shape (camelCase fields).
2. Extend `ResultService` with view-aware retrieval: resolve latest run summary for `today`, fetch all results for `all-time`, and centralize precedence rules (`runId` override, includeHidden consistency).
3. Extend `ResultRepository` with query methods that support all-time retrieval and stable ordering, plus optional helper for latest-run fallback behavior if needed.
4. Create results frontend feature module (`api`, `hooks`, `components`, `index`) with typed API client + RFC 7807-style error handling and TanStack Query keys scoped by view.
5. Add Results route and nav entry; implement `ResultsPage` tab switching via `useSearchParams` (`view=today|all-time`) and local selected-result continuity logic across refetches.
6. Implement explicit view-switch UX states: visible loading indicator, previous-content "updating" cue during refetch, and clear empty states for each view.
7. Add/adjust tests in API and frontend to cover AC behavior plus backward compatibility for `/api/results?runId=...` and camelCase response keys.

Test plan (unit/integration/API):
- API unit: extend `ResultServiceTest` and `ResultsControllerTest` for `view=today|all-time`, `runId` precedence, and `includeHidden` consistency.
- API integration: add/extend controller-level test with seeded temp SQLite data to verify latest-run resolution from `run_summaries` and cross-run all-time retrieval.
- Frontend unit/component: add `ResultsPage.test.tsx` to validate URL-driven view state, loading/updating UI, and selection retention fallback rules.
- Contract checks: assert response payload keeps camelCase keys and legacy `/api/results?runId=...` remains functional.

Likely files:
- `api/src/main/java/com/jobato/api/controller/ResultsController.java`
- `api/src/main/java/com/jobato/api/service/ResultService.java`
- `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
- `api/src/main/java/com/jobato/api/repository/RunSummaryRepository.java` (only if helper query method is needed)
- `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
- `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`
- `api/src/test/java/com/jobato/api/controller/ResultsControllerIntegrationTest.java` (new, if integration coverage is added)
- `frontend/src/features/results/api/results-api.ts`
- `frontend/src/features/results/hooks/use-results.ts`
- `frontend/src/features/results/components/ResultsPage.tsx`
- `frontend/src/features/results/components/ResultsPage.css`
- `frontend/src/features/results/components/ResultsPage.test.tsx`
- `frontend/src/features/results/index.ts`
- `frontend/src/app/router.tsx`
- `frontend/src/app/AppLayout.tsx`

## Section 4: Hard gate (commands + pass criteria)
```bash
# from repository root
./api/gradlew -p api test --tests "com.jobato.api.service.ResultServiceTest" --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.controller.ResultsControllerIntegrationTest"
```
Pass criteria:
- [ ] `view=today` returns only latest-run records (resolved via run summary metadata) with stable ordering.
- [ ] `view=all-time` returns full cross-run history from active DB with deterministic ordering.
- [ ] `includeHidden` behavior is consistent for both views.
- [ ] Backward compatibility remains: `/api/results?runId=...` still works as before.
- [ ] API response keys remain camelCase (no snake_case regressions).

## Section 5: Soft gate (frontend)
Checks:
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultsPage.test.tsx`
- [ ] `npm --prefix frontend run build`
- [ ] Manual UI check: `/results` defaults to `view=today` when param missing.
- [ ] Manual UI check: switching tabs updates URL param and triggers view-scoped query key.
- [ ] Manual UI check: prior list stays visible with an updating/loading cue during view switch.
- [ ] Manual UI check: selection is retained when item exists in next dataset; otherwise fallback first/null.
Follow-ups if failing:
- Log failing frontend checks as non-blocking with exact repro steps and screenshots/console output.
- Open a targeted follow-up task for UX/state issues while allowing backend hard-gate completion.

## Section 6: Risks and rollback
- Risks: missing or stale `run_summaries` rows can make `today` appear empty; all-time queries may grow slower as history increases; view-switch selection edge cases (deleted/hidden IDs) can cause confusing focus/selection jumps.
- Rollback steps: revert Results-page route/nav and `features/results` module; revert `/api/results` view logic to prior runId-only behavior; rerun API hard-gate tests to confirm restored baseline behavior.

## Section 7: Blockers/questions (if any)
1) None.
