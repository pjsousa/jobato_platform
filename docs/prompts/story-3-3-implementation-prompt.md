# Story 3.3 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.3 only.

STORY:
Story 3.3: Assign relevance scores (baseline)

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md
@_bmad-output/implementation-artifacts/3-2-detect-and-link-duplicates.md
@_bmad-output/implementation-artifacts/3-1-normalize-urls-for-stable-dedupe-keys.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Store baseline relevance scoring metadata and expose score fields for retrieval/sorting.

MANDATORY RULES:
- Scope is Story 3.3 only.
- Baseline score must default to 0 when no model is active.
- Score range must be constrained to [-1, 1].
- Duplicates should inherit canonical score behavior per story notes.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Add/persist `relevance_score`, `scored_at`, `score_version`.
- Integrate scoring step after dedupe in ingestion pipeline.
- Update API result DTO/service for score fields and score sorting.
- Add tests for score range and baseline/default behavior.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_scoring.py ml/tests/test_ingestion_scoring.py
2) ./gradlew test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"
3) RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
4) Poll /api/runs/$RUN_ID until terminal
5) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT MIN(relevance_score), MAX(relevance_score), COUNT(*) FROM run_items WHERE relevance_score IS NOT NULL;"

PASS CRITERIA:
- Scoring tests pass.
- API score contract tests pass.
- Stored scores are within allowed range and include metadata fields.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
