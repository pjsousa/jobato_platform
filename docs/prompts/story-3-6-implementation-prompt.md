# Story 3.6 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.6 only.

STORY:
Story 3.6: Model selection and activation

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-6-model-selection-and-activation.md
@_bmad-output/implementation-artifacts/3-5-parallel-candidate-training-and-evaluation.md
@_bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md
@_bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Enable model comparison, activation of a selected candidate, and rollback to previous versions.

MANDATORY RULES:
- Scope is Story 3.6 only.
- Activation and rollback updates must be atomic.
- New scoring runs must use the active model version.
- Keep full activation history for audit.
- Hard gate scope is backend/API/ML; frontend is soft gate.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Add model comparison and active-model APIs.
- Add model activation endpoint and persistence.
- Add rollback path to previous versions.
- Integrate scoring pipeline with active model lookup.
- Add tests for activation/rollback and active model usage.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_model_activation.py ml/tests/test_model_selector.py
2) ./gradlew test --tests "com.jobato.api.controller.MlModelControllerTest" --tests "com.jobato.api.service.MlModelClientTest"
3) curl -i http://localhost:18080/api/ml/models/comparisons
4) curl -i -X POST http://localhost:18080/api/ml/models/<modelId>/activate
5) curl -i http://localhost:18080/api/ml/models/active

PASS CRITERIA:
- Activation tests pass.
- Active model endpoint reflects activated model.
- Rollback path is validated by tests.
- Scoring pipeline records active model version.

SOFT GATE (FRONTEND):
- Validate model comparison/activation UI behavior and update frontend tests if UI changes are included.
- Do not fail hard gate for frontend-only issues; list them as follow-up items.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
