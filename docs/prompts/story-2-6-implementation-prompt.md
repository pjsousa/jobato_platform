# Story 2.6 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 2.6 only.

STORY:
Story 2.6: Run summary metrics and zero-results logging

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/2-6-run-summary-metrics-and-zero-results-logging.md
@_bmad-output/implementation-artifacts/2-5-cache-results-and-enforce-revisit-throttling.md
@_bmad-output/implementation-artifacts/2-4-capture-raw-html-and-visible-text.md
@_bmad-output/implementation-artifacts/2-3-fetch-search-results-and-persist-metadata.md
@_bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-2-prioritized-fix-plan-gated.md
@docs/epic-2-fix-plan-execution-checklist.md
@docs/guide-run-report-2026-02-11.md
@GUIDE.md

PRIMARY GOAL:
Deliver complete latest-run reporting and zero-result observability, fully wired across API/ML/UI.

MANDATORY RULES:
- Keep changes scoped to Story 2.6 only.
- Respect service boundaries (frontend/api/ml).
- API JSON camelCase; DB snake_case.
- RFC 7807 for API errors.
- Do not change event contracts unless intentionally versioned.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Persist run summaries from run completion/failure handling.
- Summary fields: runId, status, triggerTime, durationMs, newJobsCount, relevantCount.
- Persist zero-result query/domain logs linked to runId.
- Ensure GET /api/reports/runs/latest returns 200 with populated payload when data exists.
- Replace frontend run-summary placeholders with real report data.
- Add tests for API/ML/frontend summary behavior.

WORKFLOW:
1) Summarize ACs and planned files.
2) Implement code + tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and remaining risks.

GATE COMMANDS (must pass before done):
1) RUN_ID=$(curl -s -X POST http://localhost:8080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
2) Poll /api/runs/$RUN_ID until status != running
3) curl -i http://localhost:8080/api/reports/runs/latest
4) sqlite3 data/db/runs/active.db "SELECT run_id,status,duration_ms,new_jobs_count,relevant_count FROM run_summaries ORDER BY trigger_time DESC LIMIT 1;"
5) Run story tests (API/ML/frontend)

PASS CRITERIA:
- Reports endpoint returns HTTP 200 with expected summary fields.
- Latest summary row exists in run_summaries.
- Zero-result logs exist and are linked to runId.
- UI summary bar shows real values (not placeholders).

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
