# Story 3.5 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.5 only.

STORY:
Story 3.5: Parallel candidate training and evaluation

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-5-parallel-candidate-training-and-evaluation.md
@_bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md
@_bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Evaluate all candidate models in parallel with bounded worker concurrency and persist comparable metrics.

MANDATORY RULES:
- Scope is Story 3.5 only.
- Respect configured worker cap (`evalWorkers`) strictly.
- Ensure one failed model job does not stop remaining evaluations.
- Persist metrics with run/model/version linkage.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Build evaluation queue/worker pool.
- Enqueue one job per registered model.
- Compute and persist precision, recall, f1, accuracy.
- Add evaluation status/results APIs.
- Add tests for concurrency and metrics persistence.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_evaluation_worker.py ml/tests/test_metrics.py ml/tests/test_evaluation_pipeline.py
2) curl -i -X POST http://localhost:18080/api/ml/evaluations
3) curl -i http://localhost:18080/api/ml/evaluations/<evaluationId>
4) curl -i http://localhost:18080/api/ml/evaluations/<evaluationId>/results

PASS CRITERIA:
- Evaluation tests pass.
- Worker concurrency cap is validated by tests.
- Evaluation APIs return status and persisted metrics for each model.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
