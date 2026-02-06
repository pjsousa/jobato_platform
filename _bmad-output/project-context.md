---
project_name: 'jobato'
user_name: 'Pedro'
date: '2026-02-06T01:21:37+0000'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 33
optimized_for_llm: true
existing_patterns_found: 5
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- Frontend: Vite + React + TypeScript
- React Router: 7.13.0
- TanStack Query: 5.90.20
- react-window: 2.2.6
- API: Spring Boot 4.0.2.RELEASE (Java 17)
- OpenAPI: SpringDoc 3.0.1
- DB migrations: Flyway 12.0.0
- ML API: FastAPI (Python 3)
- ML data layer: SQLAlchemy 2.0.46 + Alembic 1.18.3
- Metrics: Micrometer 1.16.2 (API), prometheus-client 0.24.1 (ML)
- Storage: SQLite 3.51.2
- Messaging: Redis Streams (Redis 8.4)

## Critical Implementation Rules

### Language-Specific Rules

- TypeScript: use camelCase JSON fields and map directly to API contracts.
- TypeScript: keep server data in TanStack Query; avoid ad-hoc caches.
- TypeScript: components in PascalCase; non-component files in kebab-case.
- Java: validate inputs at controllers; return RFC 7807 Problem Details for errors.
- Java: use JDBC + Flyway only; no ORM without updating architecture.
- Java: API DTOs use camelCase JSON; no snake_case in API payloads.
- Python: SQLAlchemy/Alembic only for new SQLite files; never write to active DB after pointer swap.
- Python: event payloads must include `eventId`, `eventType`, `eventVersion`, `occurredAt`, `runId`.
- Python: configs are external; do not embed configs in SQLite.

### Framework-Specific Rules

- React: use React Router for routing; no custom router.
- React: use TanStack Query for all server data; queries defined per feature module.
- React: use react-window for results list virtualization when lists are long.
- Spring Boot: use SpringDoc for OpenAPI; controllers in `com.jobato.api.controller`.
- Spring Boot: use Actuator + Micrometer; expose `/api/metrics` and `/api/health`.
- Spring Boot: internal endpoints must require `X-Jobato-Api-Key`.
- FastAPI: pipeline logic in `ml/app/pipelines/*`; service clients in `ml/app/services/*`.
- FastAPI: publish Redis Streams events using the standard envelope; consumers idempotent.

### Testing Rules

- Frontend tests are co-located `*.test.ts(x)`; no central `/tests` folder.
- API tests live in `api/src/test/java` (JUnit default).
- ML tests live in `ml/tests/` (pytest).
- Focus unit tests on service logic and API contracts; no E2E tests in MVP.

### Code Quality & Style Rules

- Naming conventions from architecture are mandatory (snake_case DB; camelCase JSON; PascalCase React components).
- Keep feature-based folder structure; no cross-feature imports except via `shared/`.
- Avoid comments unless they clarify non-obvious logic.
- Use ASCII by default; avoid Unicode unless already present in the file.

### Development Workflow Rules

- Use Makefile targets for local dev/test/build; prefer `make dev` for multi-service.
- No CI/CD in MVP; local checks only.
- Keep `.env` files per service and exclude secrets from git.

### Critical Don't-Miss Rules

- Do not write to the active SQLite file from ML after pointer swap; only API writes to active DB.
- Never store raw/canonical HTML in SQLite; keep under `data/html/*`.
- Do not introduce snake_case in API JSON responses; keep camelCase.
- Do not bypass `X-Jobato-Api-Key` for internal endpoints.
- Keep Redis event envelope fields consistent and increment `eventVersion` on breaking changes.

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code.
- Follow ALL rules exactly as documented.
- When in doubt, prefer the more restrictive option.
- Update this file if new patterns emerge.

**For Humans:**
- Keep this file lean and focused on agent needs.
- Update when the technology stack changes.
- Review quarterly for outdated rules.
- Remove rules that become obvious over time.

Last Updated: 2026-02-06T01:21:37+0000
