# Story 2.3 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 2.3 only.

STORY:
Story 2.3: Fetch search results and persist metadata

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/2-3-fetch-search-results-and-persist-metadata.md
@_bmad-output/implementation-artifacts/2-1-manual-run-request-and-lifecycle-tracking.md
@_bmad-output/implementation-artifacts/2-2-quota-and-concurrency-enforcement.md
@_bmad-output/implementation-artifacts/1-4-generate-per-site-query-combinations.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-2-prioritized-fix-plan-gated.md
@docs/epic-2-fix-plan-execution-checklist.md
@docs/guide-run-report-2026-02-11.md
@GUIDE.md

PRIMARY GOAL:
Make run orchestration execute ingestion end-to-end without manual Redis completion simulation, and persist run_items metadata per run.

MANDATORY RULES:
- Keep changes scoped to Story 2.3 only.
- Respect service boundaries (frontend/api/ml).
- API JSON camelCase, DB snake_case.
- RFC 7807 for API errors.
- Redis event envelope must include: eventId, eventType, eventVersion, occurredAt, runId, payload.
- Use deterministic mock provider for hard gates. Real provider is optional smoke test only.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- ML must consume run.requested from Redis Streams and process payload.runInputs.
- ML must emit run.completed or run.failed from runtime.
- Replace fragile bespoke YAML parsing with proper YAML loading.
- Persist query/search context required by story (search_query, and query_id if available).
- Remove runtime create_all reliance and enforce migrations.
- Handle network/timeouts cleanly and map failures to run.failed.

WORKFLOW:
1) Summarize ACs and planned files.
2) Implement code + tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and remaining risks.

GATE COMMANDS (must pass before done):
1) docker compose up -d --build
2) RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
3) Poll /api/runs/$RUN_ID until status != running
4) sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE run_id='${RUN_ID}';"
5) docker compose exec redis redis-cli XREVRANGE ml:run-events + - COUNT 20
6) PYTHONPATH=ml python3 -m pytest ml/tests/test_ingestion.py ml/tests/test_fetcher.py ml/tests/test_results_persistence.py ml/tests/test_google_search.py

PASS CRITERIA:
- Run reaches terminal state without manual XADD completion.
- run_items exists and has rows for runId (for non-empty inputs).
- Redis shows matching run.requested and ML completion/failure event.
- Target tests pass.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
