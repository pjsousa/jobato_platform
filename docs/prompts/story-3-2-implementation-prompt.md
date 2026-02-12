# Story 3.2 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 3.2 only.

STORY:
Story 3.2: Detect and link duplicates

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/3-2-detect-and-link-duplicates.md
@_bmad-output/implementation-artifacts/3-1-normalize-urls-for-stable-dedupe-keys.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-3-prioritized-fix-plan-gated.md
@docs/epic-3-fix-plan-execution-checklist.md

PRIMARY GOAL:
Detect exact and near duplicates, link them to canonical records, and hide duplicates by default in API retrieval.

MANDATORY RULES:
- Scope is Story 3.2 only.
- Depend on Story 3.1 normalized URL key flow.
- Preserve all duplicate rows (hide by default, do not delete).
- Maintain idempotent dedupe behavior.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Add canonical linkage fields (`canonical_id`, `is_duplicate`, `is_hidden`, `duplicate_count`).
- Implement exact dedupe on normalized URL.
- Implement text similarity dedupe with explicit threshold.
- Keep canonical as first-seen record.
- Update API retrieval behavior: hidden duplicates excluded by default.
- Add targeted tests for URL-match and text-similarity matching.

WORKFLOW:
1) Summarize acceptance criteria and target files.
2) Implement code and tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and risks.

GATE COMMANDS:
1) PYTHONPATH=ml python3 -m pytest ml/tests/test_dedupe.py ml/tests/test_ingestion_dedupe.py
2) ./gradlew test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"
3) RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
4) Poll /api/runs/$RUN_ID until terminal
5) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE is_duplicate = 1;"
6) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE canonical_id IS NOT NULL;"

PASS CRITERIA:
- Dedupe tests pass.
- API tests for hidden-by-default behavior pass.
- Canonical linkage exists where duplicates are detected.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
