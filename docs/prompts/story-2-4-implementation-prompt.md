# Story 2.4 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 2.4 only.

STORY:
Story 2.4: Capture raw HTML and visible text

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/2-4-capture-raw-html-and-visible-text.md
@_bmad-output/implementation-artifacts/2-3-fetch-search-results-and-persist-metadata.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-2-prioritized-fix-plan-gated.md
@docs/epic-2-fix-plan-execution-checklist.md
@docs/guide-run-report-2026-02-11.md
@GUIDE.md

PRIMARY GOAL:
Capture HTML and visible text reliably for ingested results, with per-item error resilience and correct DB/file linkage.

MANDATORY RULES:
- Keep changes scoped to Story 2.4 only.
- Respect service boundaries (frontend/api/ml).
- Raw HTML must stay in file storage; SQLite stores path/text/errors only.
- API JSON camelCase, DB snake_case.
- Use deterministic mock provider for hard gates.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Persist raw HTML under deterministic paths in data/html/raw.
- Persist raw_html_path and visible_text on each result.
- Persist fetch_error/extract_error while continuing run.
- Ensure UTF-8 and malformed HTML resilience.
- Align model + migration + runtime schema.

WORKFLOW:
1) Summarize ACs and planned files.
2) Implement code + tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and remaining risks.

GATE COMMANDS (must pass before done):
1) RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
2) Poll /api/runs/$RUN_ID until status != running
3) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE raw_html_path IS NOT NULL;"
4) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE visible_text IS NOT NULL AND length(visible_text) > 0;"
5) HTML_PATH=$(sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT raw_html_path FROM run_items WHERE raw_html_path IS NOT NULL LIMIT 1;")
6) test -f "$HTML_PATH" && echo "OK"
7) PYTHONPATH=ml python3 -m pytest ml/tests/test_html_services.py ml/tests/test_ingestion_html_integration.py

PASS CRITERIA:
- At least one row has raw_html_path and visible_text.
- Referenced HTML file exists on disk.
- HTML-related tests pass.
- Per-item errors do not abort the full run.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
