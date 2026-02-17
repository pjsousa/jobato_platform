# Story 3.7 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.7 only.

STORY:
Story 3.7: Daily retrain for the active model

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-7-daily-retrain-for-the-active-model.md
@_bmad-output/implementation-artifacts/3-6-model-selection-and-activation.md
@_bmad-output/implementation-artifacts/3-5-parallel-candidate-training-and-evaluation.md
@_bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Run daily retraining for the active model, version new artifacts, and keep scoring on the latest validated active version.

MANDATORY RULES:
- Scope is Story 3.7 only.
- Retrain must be safe: previous active model remains fallback on failure.
- No-label retrain must complete cleanly as skipped, not failed.
- Keep retrain history and status queryable.
- Hard gate scope is backend/API/ML; frontend is soft gate.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Add scheduler for daily retrain and manual trigger endpoint.
- Implement retrain pipeline with new model version generation.
- Persist retrain job history/status.
- Integrate retrained active version into scoring usage.
- Add no-new-label handling and failure safety.
- Add tests for scheduler, retrain flow, and no-label path.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_retrain_scheduler.py ml/tests/test_retrain_pipeline.py ml/tests/test_retrain_no_labels.py
2) ./gradlew test --tests "com.jobato.api.controller.RetrainControllerTest"
3) curl -i -X POST http://localhost:18080/api/ml/retrain/trigger
4) curl -i http://localhost:18080/api/ml/retrain/status
5) curl -i http://localhost:18080/api/ml/retrain/history

PASS CRITERIA:
- Retrain tests pass.
- Manual trigger/status/history APIs work.
- Retrain creates new version when labels exist.
- No-label path returns skipped and keeps current active model.

SOFT GATE (FRONTEND):
- Validate retrain status/history/trigger UI behavior and update frontend tests if UI changes are included.
- Do not fail hard gate for frontend-only issues; list them as follow-up items.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
