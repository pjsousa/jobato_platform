# Story 3.4 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.4 only.

STORY:
Story 3.4: Pluggable model interface and registry

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md
@_bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Provide a model plugin contract and startup-discovered registry so scoring can select models without core pipeline edits.

MANDATORY RULES:
- Scope is Story 3.4 only.
- Keep registry config external (no hardcoded model list).
- Invalid model modules must not block valid model loading.
- Preserve baseline fallback behavior if no valid model is available.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Define model interface contract (fit/predict).
- Implement registry loader and discovery from config.
- Initialize registry on ML service startup.
- Expose discovered model identifiers.
- Add clear error reporting for invalid model entries.
- Add tests for contract validation and registry error isolation.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_model_interface.py ml/tests/test_registry.py
2) curl -i http://localhost:8000/health
3) curl -i http://localhost:8000/ml/models

PASS CRITERIA:
- Registry/interface tests pass.
- ML service starts and exposes discovered models.
- Invalid plugins are reported but do not break startup.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
