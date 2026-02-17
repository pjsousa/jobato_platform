# Story 3.1 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.1 only.

STORY:
Story 3.1: Normalize URLs for stable dedupe keys

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-1-normalize-urls-for-stable-dedupe-keys.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Generate and persist deterministic normalized URL keys for ingested results without breaking pipeline stability.

MANDATORY RULES:
- Scope is Story 3.1 only.
- Keep service boundaries strict (frontend/api/ml).
- DB schema fields in snake_case, API JSON in camelCase.
- Never crash ingestion on malformed URL; log and continue.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Normalize URLs for stable dedupe key generation.
- Strip tracking parameters and fragments; normalize host/scheme casing.
- Persist normalized key in run-items storage.
- Preserve original raw URL.
- Add tests for equivalence and malformed URL handling.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_url_normalization.py ml/tests/test_ingestion.py
2) RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
3) Poll /api/runs/$RUN_ID until terminal
4) sqlite3 "data/db/runs/${RUN_ID}.db" "PRAGMA table_info(run_items);"
5) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE normalized_url IS NOT NULL;"

PASS CRITERIA:
- Tests pass.
- `normalized_url` column exists.
- Ingested rows include non-null normalized URL values.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
