# Story 4.6 Plan

## Section 1: Scope and assumptions
- In scope:
  - Enforce deterministic first-seen ordering in API read paths using `createdAt` as first-seen source (`DESC`, tie-breaker `id DESC`).
  - Apply the same ordering policy to `/api/results` and `/api/results/by-query` without changing duplicate-hiding behavior (`includeHidden`).
  - Keep Today/All Time ordering behavior consistent and preserve selected item by stable `id` when possible.
  - Add focused tests for ordering stability and selection continuity.
- Out of scope:
  - Story 4.7 keyboard/accessibility interaction matrix.
  - Any new ranking heuristics using `relevanceScore`.
  - Changes to feedback cycle semantics from Stories 4.4/4.5.
  - Broad schema redesign; `createdAt` remains canonical first-seen source unless `firstSeenAt` already exists.
- Dependencies:
  - Direct dependencies: Stories 4.1, 4.2, 4.3, 4.4, 4.5.
  - Assumption: Results/feedback frontend baseline exists on the target integration branch; in current tree `frontend/src/features/results` and `frontend/src/features/feedback` are absent, so frontend validation is soft-gated and logged.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1: list sorted by first seen desc and stable across refresh | Update repository SQL ordering to deterministic `ORDER BY created_at DESC, id DESC` in both run and run+query reads; keep `includeHidden` filter unchanged; ensure API exposes camelCase timestamp fields and no competing API-side reorder logic. | API/repository tests for deterministic tie-breaker when `created_at` is identical; controller tests for `/api/results` and `/api/results/by-query` response ordering path and camelCase fields. | Hard gate passes when API tests return exit code 0 and ordering assertions confirm timestamp-desc + id-desc stability. |
| AC2: consistent sort across view switch and selection preserved | Keep one authoritative sort policy (API order first). In frontend results state, preserve selected `id` on view/refetch when still visible; fallback to first visible item or empty-detail state when not visible. | Frontend tests for Today/All Time consistency, refresh stability, and selection preservation/fallback behavior. | Soft gate logs pass/fail from frontend tests/build; failures are non-blocking but recorded with follow-up actions. |

## Section 3: Implementation plan (task list)
1. Validate story boundaries and prerequisites for 4.6 only (no 4.7/relevance-ranking work), and confirm first-seen source remains `createdAt` in this story.
2. Implement deterministic backend ordering in `ResultRepository` for both list query paths (`created_at DESC, id DESC`) while preserving existing `includeHidden` semantics.
3. Keep API/service contracts stable (camelCase responses, no snake_case additions, no behavior drift for counts/filter endpoints).
4. Implement/align frontend ordering behavior to consume API order (or stable immutable comparator fallback only if needed), and preserve selection by `id` across view switch/refetch.
5. Add targeted tests:
   - Unit/API: repository/controller/service coverage for deterministic ordering and unchanged hidden-duplicate behavior.
   - Frontend: ordering consistency in Today/All Time, refresh stability, and selection continuity/fallback.

Likely files:
- `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
- `api/src/main/java/com/jobato/api/service/ResultService.java`
- `api/src/main/java/com/jobato/api/controller/ResultsController.java`
- `api/src/main/java/com/jobato/api/model/ResultItem.java` (only if optional `firstSeenAt` alias is introduced)
- `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
- `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`
- `api/src/test/java/com/jobato/api/repository/ResultRepositoryOrderingTest.java` (new)
- `frontend/src/features/results/api/results-api.ts`
- `frontend/src/features/results/hooks/use-results.ts`
- `frontend/src/features/results/components/ResultsPage.tsx`
- `frontend/src/features/results/components/ResultsList.tsx`
- `frontend/src/features/results/components/ResultDetail.tsx`
- `frontend/src/features/results/components/ResultsPage.test.tsx`
- `frontend/src/features/results/components/ResultsList.test.tsx`
- `frontend/src/features/results/components/ResultDetail.test.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/app/AppLayout.tsx`

## Section 4: Hard gate (commands + pass criteria)
```bash
# API deterministic ordering and contract checks (blocking)
cd api && ./gradlew test --tests "com.jobato.api.repository.ResultRepositoryOrderingTest" --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"

# API full regression suite (blocking)
cd api && ./gradlew test
```
Pass criteria:
- [ ] All hard-gate commands exit with code 0.
- [ ] Deterministic ordering is proven by tests for equal timestamps (`created_at DESC`, then `id DESC`).
- [ ] `/api/results` and `/api/results/by-query` preserve duplicate-hiding behavior (`includeHidden`) while applying deterministic order.
- [ ] API payloads remain camelCase (`createdAt`, `lastSeenAt`, optional `firstSeenAt`) with no snake_case regressions.

## Section 5: Soft gate (frontend)
Checks:
- [ ] Results feature baseline exists (`frontend/src/features/results/*` present) and route/nav wiring for Results is available.
- [ ] Ordering in Today and All Time is consistent with first-seen policy and remains stable after refetch.
- [ ] Selection is preserved across view switch when selected item remains visible; fallback behavior is correct when it does not.
- [ ] Frontend checks run successfully:
  - `cd frontend && npm run test -- src/features/results/components/ResultsPage.test.tsx src/features/results/components/ResultsList.test.tsx src/features/results/components/ResultDetail.test.tsx`
  - `cd frontend && npm run build`
Follow-ups if failing:
- Log soft-gate failure details in story notes (missing baseline vs regression).
- If baseline files are missing, create prerequisite task(s) for Story 4.1-4.5 artifacts and re-run soft gate after baseline is present.
- If behavior regresses, ship backend fix only if hard gate passes, and keep story status short of done until soft-gate checks are green.

## Section 6: Risks and rollback
- Risks:
  - `created_at` ordering assumes ISO-8601 sortable timestamps; malformed timestamps can degrade ordering predictability.
  - Missing frontend baseline in current tree can prevent full AC2 validation even when backend is correct.
  - Introducing `firstSeenAt` without strict backward compatibility can cause client contract drift.
- Rollback steps:
  - Revert repository ordering changes to prior query behavior and remove any optional `firstSeenAt` response additions.
  - Revert dependent API/controller/frontend sort-consistency changes introduced in this story.
  - Re-run hard-gate API tests to confirm baseline behavior is restored.
  - Re-run soft-gate frontend checks and document residual gaps.

## Section 7: Blockers/questions (if any)
None.
