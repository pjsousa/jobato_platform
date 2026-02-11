# Story 2.5 - Agent Prompt

```md
You are the implementation agent for Jobato. Implement Story 2.5 only.

STORY:
Story 2.5: Cache results and enforce revisit throttling

CONTEXT FILES (read first, in order):
@_bmad-output/implementation-artifacts/2-5-cache-results-and-enforce-revisit-throttling.md
@_bmad-output/implementation-artifacts/2-4-capture-raw-html-and-visible-text.md
@_bmad-output/implementation-artifacts/2-3-fetch-search-results-and-persist-metadata.md
@_bmad-output/implementation-artifacts/2-2-quota-and-concurrency-enforcement.md
@_bmad-output/planning-artifacts/epics.md
@_bmad-output/planning-artifacts/architecture.md
@project-context.md
@docs/epic-2-prioritized-fix-plan-gated.md
@docs/epic-2-fix-plan-execution-checklist.md
@docs/guide-run-report-2026-02-11.md
@GUIDE.md

PRIMARY GOAL:
Enforce real cache reuse (12h TTL) and URL revisit throttle (7 days) in the live ingestion path.

MANDATORY RULES:
- Keep changes scoped to Story 2.5 only.
- Respect service boundaries (frontend/api/ml).
- DB snake_case, API JSON camelCase.
- Use deterministic mock provider for hard gates.
- If blocked, ask exactly one targeted question with a recommended default.

MANDATORY IMPLEMENTATION REQUIREMENTS:
- Cache lookup must occur before external search call.
- Fresh cache must short-circuit external call.
- Persist and enforce cache metadata: cache_key, cached_at, cache_expires_at.
- Revisit throttle before HTML fetch; persist skip_reason='revisit_throttle'.
- Read TTL and throttle values from config.
- Add tests for TTL boundary and 7-day cutoff.

WORKFLOW:
1) Summarize ACs and planned files.
2) Implement code + tests.
3) Run gate commands exactly.
4) Return AC -> evidence mapping and remaining risks.

GATE COMMANDS (must pass before done):
1) Trigger Run A and wait terminal.
2) Trigger Run B with same enabled inputs and wait terminal.
3) docker compose logs ml --tail 400 | python3 -c "import sys; t=sys.stdin.read(); print('cache.hit' in t)"
4) sqlite3 "data/db/runs/${RUN_B}.db" "SELECT COUNT(*) FROM run_items WHERE cache_key IS NOT NULL;"
5) sqlite3 "data/db/runs/${RUN_B}.db" "SELECT COUNT(*) FROM run_items WHERE skip_reason='revisit_throttle';"
6) PYTHONPATH=ml python3 -m pytest ml/tests/test_cache*.py

PASS CRITERIA:
- Cache-hit behavior is observable in logs/metrics.
- Cache metadata is persisted.
- Revisit throttle is observable when repeated URLs exist.
- Cache/revisit tests pass.

OUTPUT FORMAT:
- Section 1: What changed
- Section 2: Acceptance Criteria validation table
- Section 3: Gate results (pass/fail per check)
- Section 4: Risks or unresolved items
```
