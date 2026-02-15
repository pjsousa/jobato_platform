# Story 4-4 Plan

## Section 1: Scope and assumptions
- In scope: implement Story 4.4 only - tri-state manual feedback (`relevant -> irrelevant -> null`) via title activation, immediate UI state update, persisted feedback via `POST /api/feedback`, clear-label behavior, and `manualLabel` hydration in results payloads.
- Out of scope: Story 4.5-4.7 behaviors (irrelevant visibility toggle, first-seen sorting changes, expanded keyboard matrix), model-training/scoring changes, and any redesign of Results UX beyond label cycle/pill updates.
- Dependencies: Story 4.1-4.3 baseline must already exist (`/results` route/nav, Results page/list/detail components, URL `view` state handling, stable identity fields in API responses). Current repository scan shows those frontend artifacts are missing, so this is a real prerequisite gate.
- Assumptions: first activation from `null` sets `manualLabel` to `relevant`; persistence identity resolution is canonical-first with normalized-URL fallback; API JSON remains camelCase and RFC 7807 is used for validation/domain errors.

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|
| AC1 - title click cycles Relevant -> Irrelevant -> None and list pill updates | Add feedback mutation flow and deterministic next-label function in Results detail/title interaction; update selected item title state and list pill immediately; render no pill when state is `null`. | Frontend: `ResultDetail.test.tsx` + `ResultsPage.test.tsx` cycle-order and pill-visibility tests. | Soft-gate tests pass and manual click path at `/results` shows exact cycle order with immediate list/detail sync. |
| AC2 - UI updates immediately and label persists | Implement `POST /api/feedback` with validated tri-state payload and stable-identity persistence; wire TanStack Query optimistic update (`onMutate` snapshot, rollback on error, invalidate on settle). | API: `FeedbackControllerTest`, `FeedbackServiceTest`; Frontend: optimistic update/rollback test. | Hard-gate API tests pass for set relevant, set irrelevant, clear, and invalid payload; soft-gate confirms optimistic UI + rollback behavior. |
| AC3 - reappearing job label can be cleared and clear persists | Resolve feedback target by canonical-first identity with normalized URL fallback; include `manualLabel` and `manualLabelUpdatedAt` in `/api/results` and `/api/results/{id}` so reappearing records hydrate prior label and can be cleared to `null`. | API: reappearance mapping and clear-persistence scenarios in `FeedbackServiceTest` and updated `ResultsControllerTest`/`ResultServiceTest`. | Hard-gate tests verify prior label rehydrates on reappearance and clearing remains persisted after subsequent reads. |

## Section 3: Implementation plan (task list)
1. Run prerequisite verification for Story 4.1-4.3 artifacts; if missing, log blocker and keep Story 4.4 scoped (do not implement earlier stories inside this one).
2. Define feedback contract: `FeedbackRequest`/`FeedbackResponse`, tri-state label validation, explicit controller error handling (RFC 7807), and camelCase response fields.
3. Implement backend feedback write/read path: add `FeedbackController`, `FeedbackService`, and `FeedbackRepository` with canonical-first + normalized-url fallback identity resolution and clear-to-null persistence.
4. Extend result-read mapping so `/api/results` and `/api/results/{id}` include `manualLabel` and `manualLabelUpdatedAt` without altering duplicate visibility semantics.
5. Implement frontend feedback feature module (`feedback-api`, `use-feedback`) and integrate optimistic mutation with rollback-safe cache updates and race-condition guard while mutation is pending.
6. Wire Results UI interaction: title activation cycles label deterministically, list/detail state pills update instantly, and selected item/view mode state remain stable.
7. Add targeted tests for AC1-AC3 across API and frontend, including invalid payload handling and reappearing-job clear behavior.
8. Execute hard gate first (blocking), then soft gate (non-blocking) and record outcomes with failing checks explicitly logged.

Test plan (unit/integration/API):
- API unit/service: stable-identity resolution, set/overwrite/clear behavior, and null-clear persistence semantics.
- API controller/contract: valid tri-state payloads accepted, invalid labels rejected with RFC 7807 response, and results endpoints expose `manualLabel` fields in camelCase.
- Frontend component tests: title cycle order, immediate list/detail pill sync, no-pill rendering for `null`, optimistic rollback on API failure, and pending-mutation multi-click guard.
- Frontend integration-style check: selected result remains selected after mutation and URL-driven view state is preserved.

Likely files:
- `api/src/main/java/com/jobato/api/controller/FeedbackController.java`
- `api/src/main/java/com/jobato/api/controller/ResultsController.java`
- `api/src/main/java/com/jobato/api/service/FeedbackService.java`
- `api/src/main/java/com/jobato/api/service/ResultService.java`
- `api/src/main/java/com/jobato/api/repository/FeedbackRepository.java`
- `api/src/main/java/com/jobato/api/repository/ResultRepository.java`
- `api/src/main/java/com/jobato/api/repository/ActiveRunDatabase.java`
- `api/src/main/java/com/jobato/api/model/FeedbackLabel.java`
- `api/src/main/java/com/jobato/api/model/ResultItem.java`
- `api/src/main/java/com/jobato/api/dto/FeedbackRequest.java`
- `api/src/main/java/com/jobato/api/dto/FeedbackResponse.java`
- `api/src/test/java/com/jobato/api/controller/FeedbackControllerTest.java`
- `api/src/test/java/com/jobato/api/controller/ResultsControllerTest.java`
- `api/src/test/java/com/jobato/api/service/FeedbackServiceTest.java`
- `api/src/test/java/com/jobato/api/service/ResultServiceTest.java`
- `frontend/src/features/feedback/api/feedback-api.ts`
- `frontend/src/features/feedback/hooks/use-feedback.ts`
- `frontend/src/features/feedback/index.ts`
- `frontend/src/features/results/api/results-api.ts`
- `frontend/src/features/results/hooks/use-results.ts`
- `frontend/src/features/results/components/ResultsPage.tsx`
- `frontend/src/features/results/components/ResultsList.tsx`
- `frontend/src/features/results/components/ResultDetail.tsx`
- `frontend/src/features/results/components/ResultsPage.test.tsx`
- `frontend/src/features/results/components/ResultDetail.test.tsx`
- `frontend/src/features/results/index.ts`

## Section 4: Hard gate (commands + pass criteria)
```bash
# from repository root
./api/gradlew -p api test --tests "com.jobato.api.controller.FeedbackControllerTest" --tests "com.jobato.api.service.FeedbackServiceTest" --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"
```
Pass criteria:
- [ ] Command exits with code 0.
- [ ] API tests verify tri-state write behavior (`relevant`, `irrelevant`, `null`) and invalid label payload rejection via RFC 7807 response shape.
- [ ] API tests verify `/api/results` and `/api/results/{id}` include `manualLabel` and `manualLabelUpdatedAt` in camelCase.
- [ ] API tests verify reappearing-job identity mapping (canonical-first, normalized-url fallback) and clear-label persistence.
- [ ] Any failure in the command above is a hard-gate failure (story cannot pass implementation gate).

## Section 5: Soft gate (frontend)
Checks:
- [ ] `npm --prefix frontend run test -- src/features/results/components/ResultDetail.test.tsx src/features/results/components/ResultsPage.test.tsx`
- [ ] `npm --prefix frontend run build`
- [ ] Manual check (desktop): clicking selected title cycles `Relevant -> Irrelevant -> None`; title style and list pill update immediately.
- [ ] Manual check (desktop/mobile): no pill appears for `None`, and selected item plus URL view state are preserved after label changes.
- [ ] Manual check (error path): force API failure and confirm optimistic state rolls back with visible actionable error.
Follow-ups if failing:
- Log each soft-gate failure with repro steps (viewport, URL, click sequence, expected vs actual).
- Open targeted follow-up tasks for UI regressions while keeping hard-gate backend status explicit.

## Section 6: Risks and rollback
- Risks: Story 4.1-4.3 baseline is not present in the current branch; feedback persistence may drift if stable identity resolution is inconsistent for duplicates/canonical records; rapid multi-clicks can cause mutation races; persistence may be lost if active DB switching does not carry feedback data forward.
- Rollback steps: remove feedback mutation wiring from Results UI, revert `manualLabel` fields from results response mapping, revert feedback controller/service/repository additions, and rerun hard-gate tests to confirm baseline behavior is restored.

## Section 7: Blockers/questions (if any)
1) Stories 4.1-4.3 artifacts are currently missing in this repository snapshot (no `frontend/src/features/results/*`, no `frontend/src/features/feedback/*`, no `/results` route/nav). Should Story 4.4 remain blocked until those prerequisites are merged? (Recommended: Yes - treat this as a blocker and start Story 4.4 only after 4.1-4.3 baseline is present.)
