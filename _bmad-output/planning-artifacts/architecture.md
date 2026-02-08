---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/product-brief-jobato-2026-02-05.md
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/prd.md
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/ux-design-specification.md
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-02-06T01:11:07+0000'
project_name: 'jobato'
user_name: 'Pedro'
date: '2026-02-06T00:16:44+0000'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
- Query/allowlist configuration (FR1–FR5): users manage query strings and allowlisted domains, enabling/disabling each.
- Run orchestration (FR6–FR10): manual run trigger, concurrency controls, quota enforcement, and run lifecycle tracking.
- Ingestion & data capture (FR11–FR18): Google search results fetch, URL handling, HTML/text capture, caching, and revisit throttling.
- Deduplication (FR19–FR22): URL normalization, similarity detection, canonical linking, duplicate hiding.
- Relevance scoring & feedback (FR23–FR27): score -1..1, daily retrain, and user labeling flow.
- Results review UI (FR28–FR33): Today/All Time views, sorting, labels, and key metadata display.
- Run reporting & status (FR34–FR37): status indicators, run metrics, quota errors, and zero-result logging.

**Non-Functional Requirements:**
- Performance: Today/All Time views load within 2 seconds.
- Reliability: runs succeed at least 95% of the time with visible failure states.
- Security: encryption at rest and in transit; no auth required in MVP.
- Accessibility: target WCAG AA compliance.
- Platform: modern browsers only; no SEO; desktop-first UX.

**Scale & Complexity:**
Low complexity, single-user system with a modest data pipeline and feedback loop.

- Primary domain: web app with backend data pipeline/ML scoring.
- Complexity level: low
- Estimated architectural components: 7–9 major subsystems (ingestion, orchestration, storage, dedupe, scoring, API, UI, feedback loop)

### Technical Constraints & Dependencies

- Google search quota limits drive strict quota accounting and caching.
- Allowlisted domain constraints for query generation.
- URL revisit throttling (>= 1 week) and result caching (12-hour TTL).
- Manual-run MVP; scheduled runs deferred.
- Desktop-first UI with defined breakpoints and keyboard-friendly interactions.

### Cross-Cutting Concerns Identified

- Quota management and caching strategies.
- Deduplication and canonicalization consistency.
- Relevance feedback loop affecting scoring and UI state.
- Observability and run status transparency.
- Accessibility and consistent interaction patterns.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application with a SPA frontend, a Java Spring API, and a Python ML/data service, all dockerized for local-first use.

### Starter Options Considered

**Frontend (SPA)**
- **Vite + React + TypeScript** (chosen): matches split-panel wireframes, strong ecosystem, fast iteration, beginner-friendly docs.
- **Vue + Vite** (alternative): similar benefits, but less aligned with broad learning resources for a new frontend.

**API Service**
- **Spring Boot (Spring Initializr)** (chosen): aligns with Java preference; clean REST API foundation with validation and data access.

**ML/Data Service**
- **FastAPI** (chosen): Python-native, quick to iterate for training/inference endpoints, excellent docs and dev CLI.

### Selected Starter: Multi-service baseline (Vite React + Spring Boot + FastAPI)

**Rationale for Selection:**
- Fits language preferences (Java/Python/TypeScript).
- Supports the split-triage SPA UX and fast feedback loop.
- Cleanly separates data processing from API orchestration.
- Docker-friendly and local-first.

**Initialization Commands:**

```bash
# Frontend (Vite + React + TypeScript)
npm create vite@latest jobato-frontend -- --template react-ts

# API (Spring Boot via Spring Initializr, Java 17, Gradle)
curl -L "https://start.spring.io/starter.zip?type=gradle-project&language=java&bootVersion=3.5.10.RELEASE&javaVersion=17&dependencies=web,validation,data-jdbc&name=jobato-api&packageName=com.jobato.api&baseDir=jobato-api" -o jobato-api.zip

# ML/Data service (FastAPI)
python -m venv .venv
source .venv/bin/activate
pip install "fastapi[standard]"
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- TypeScript for frontend, Java 17 for API, Python 3 for ML/data service.

**Styling Solution:**
- Vite React template provides minimal styling setup; use CSS modules or a light utility layer to match the wireframes' clean, neutral design.

**Build Tooling:**
- Vite for fast frontend builds and HMR.
- Gradle-based Spring Boot build for API.
- Python virtualenv with FastAPI CLI for ML/dev.

**Testing Framework:**
- Vite starter does not include tests by default; add Vitest later.
- Spring Boot provides JUnit setup by default.
- FastAPI uses pytest + httpx when tests are added.

**Code Organization:**
- Clear service boundaries: `frontend/`, `api/`, `ml/`.
- Keep ML service focused on ingestion, scoring, and model retraining.

**Development Experience:**
- Fast local iteration (Vite dev server, Spring Boot dev tools, FastAPI `fastapi dev`).
- Docker compose can standardize local-first runtime.

**Note:** Project initialization using these commands should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Data architecture: multi-SQLite files per ML run with a stable pointer file; API reads/writes active DB; ML writes to a copy, swaps pointer, then never writes to the active DB.
- Service communication: Redis Streams for ML ↔ API eventing.
- Deployment baseline: Docker Compose local-first with shared volumes.

**Important Decisions (Shape Architecture):**
- Data access tooling: JDBC + Flyway 12.0.0 for API; SQLAlchemy 2.0.46 + Alembic 1.18.3 for ML.
- Authentication & security: no UI auth in MVP; ML → API API key; HTTPS for browser → API; OS disk encryption.
- API conventions: REST + JSON; OpenAPI docs (SpringDoc 2.7.0 + FastAPI built-ins); RFC 7807 error format.
- Frontend architecture: React Router 7.13.0; TanStack Query 5.90.20 for server state; react-window 2.2.6 for list virtualization; feature-based structure.
- Monitoring/logging: structured JSON logs + health endpoints; metrics via Spring Boot Actuator + Micrometer 1.16.2 and Python prometheus-client 0.24.1.

**Deferred Decisions (Post-MVP):**
- CI/CD pipeline (GitHub Actions).
- Rate limiting.
- Full observability stack (OpenTelemetry).
- Multi-user auth/RBAC.
- Cloud hosting and scaling strategy.

### Data Architecture

- **Database engine:** SQLite 3.51.2 (local-first).
- **Storage model:** multiple SQLite files per ML run in a shared location.
- **Active DB selection:** stable pointer file (e.g., `current-db.txt`) updated by ML after each run.
- **Write model:** ML writes to a new copy, swaps pointer, then never writes to the active DB; API can write to the active DB; no concurrent writes.
- **Data scope:** SQLite stores only post-processed data and metadata; raw/canonical HTML stored outside the DB; configs are external.
- **Data access:** API uses JDBC + Flyway 12.0.0; ML uses SQLAlchemy 2.0.46 + Alembic 1.18.3.
- **Validation:** DB constraints + app-level validation in API/ML services.
- **Caching policy:** enforce 12-hour TTL and 1-week revisit throttle in ingestion pipeline; schema includes metadata for last-seen and expiry (implementation details deferred).

### Authentication & Security

- **UI auth:** none for MVP.
- **Service auth:** ML → API uses shared API key header for pointer updates and run events.
- **Encryption at rest:** rely on host OS disk encryption.
- **Encryption in transit:** HTTPS for browser → API (self-signed locally); ML → API over Docker network without TLS.
- **Secret handling:** env files or Docker secrets; excluded from git.

### API & Communication Patterns

- **API style:** REST + JSON.
- **Docs:** OpenAPI with SpringDoc 2.7.0 + FastAPI built-in docs.
- **Errors:** RFC 7807 Problem Details.
- **Rate limiting:** none for MVP.
- **Service communication:** Redis Streams on Redis Open Source 8.4; at-least-once delivery with idempotent consumers and consumer groups.

### Frontend Architecture

- **Routing:** React Router 7.13.0.
- **State management:** TanStack Query 5.90.20 for server state; React local state + context for UI state.
- **Component structure:** feature-based folders (`features/*`) plus `shared/ui`.
- **Performance:** route-based code splitting with `React.lazy`; results list virtualization via react-window 2.2.6.
- **Bundling:** default Vite build.

### Infrastructure & Deployment

- **Hosting:** local Docker Compose only.
- **Dev tooling:** Makefile drives build/test/run tasks.
- **Config:** per-service `.env` + shared `config/` volume.
- **Logging/monitoring:** structured JSON logs to stdout; health endpoints; metrics endpoints via Spring Boot Actuator + Micrometer 1.16.2 and Python prometheus-client 0.24.1.
- **Scaling:** single-node local-first; no HA.

### Decision Impact Analysis

**Implementation Sequence:**
1. Define repo layout and Docker Compose (frontend, API, ML, Redis, shared volumes).
2. Scaffold API (Spring Boot + JDBC + Flyway + SpringDoc + Actuator).
3. Scaffold ML service (FastAPI + SQLAlchemy + Alembic + prometheus-client).
4. Implement Redis Streams contracts and idempotent consumers.
5. Implement SQLite file lifecycle + pointer swap API.
6. Scaffold frontend (routing + TanStack Query + virtualization).
7. Wire TLS for browser → API and API key secrets for ML → API.
8. Add structured logging + health/metrics endpoints.

**Cross-Component Dependencies:**
- Redis Streams defines the ML → API event contract and idempotency requirements.
- Pointer file lifecycle impacts API cache invalidation and frontend freshness.
- HTTPS + API key require aligned env config across services.
- Shared config volume is required for pointer file access and runtime configuration.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
5 areas where AI agents could make different choices (naming, structure, formats, communication, process)

### Naming Patterns

**Database Naming Conventions:**
- Tables: snake_case, plural (`runs`, `run_items`)
- Columns: snake_case (`created_at`, `run_id`)
- Primary key: `id`
- Foreign keys: `<table>_id` (`run_id`)
- Indexes: `idx_<table>__<column>` (`idx_runs__created_at`)

**API Naming Conventions:**
- Base path: `/api`
- Resource paths: plural nouns (`/api/runs`, `/api/run-items`)
- Path params: `{id}` (`/api/runs/{id}`)
- Query params: camelCase (`runId`, `updatedAfter`)
- Headers: `X-Jobato-Api-Key`

**Code Naming Conventions:**
- React components: PascalCase (`RunList`)
- Component files: PascalCase (`RunList.tsx`)
- Non-component files: kebab-case (`run-api.ts`, `format-date.ts`)
- Hooks: `useX` in `use-x.ts` (`useRunFilters`)
- Java: PascalCase classes; lowercase packages
- Python: snake_case modules

### Structure Patterns

**Project Organization:**
- Top-level folders: `frontend/`, `api/`, `ml/`, `infra/`, `config/`, `scripts/`, `data/` (gitignored), optional `docs/`
- No cross-service shared code; each service owns its utilities.

**File Structure Patterns:**
- Frontend:
  - `frontend/src/app` (routes/providers)
  - `frontend/src/features/*`
  - `frontend/src/shared/ui`, `frontend/src/shared/lib`
  - `frontend/src/assets`, `frontend/public`
- API (Spring):
  - `com.jobato.api.controller`, `service`, `repository`, `model`, `dto`, `config`
- ML (FastAPI):
  - `ml/app`, `ml/pipelines`, `ml/services`, `ml/db`, `ml/models`, `ml/schemas`
- Tests:
  - Frontend: co-located `*.test.ts(x)`
  - API: `api/src/test/java`
  - ML: `ml/tests/`
- Config & env:
  - Per-service `.env`
  - Shared `config/` mounted into containers

### Format Patterns

**API Response Formats:**
- Success: direct resource (no wrapper)
- Lists: JSON arrays
- Extra metadata only when needed: `{items: [...], meta: {...}}`
- Errors: RFC 7807 Problem Details with `type`, `title`, `status`, `detail`, `instance`, `errorCode`

**Data Exchange Formats:**
- JSON fields: camelCase
- Dates: ISO 8601 UTC strings (`2026-02-06T14:12:00Z`)
- Booleans: true/false
- Nulls: explicit `null` only when value is unknown or unavailable

### Communication Patterns

**Event System Patterns (Redis Streams):**
- Stream: `ml:run-events`
- Event naming: dot-lowercase (`run.completed`, `run.failed`)
- Payload envelope (camelCase):
  - `eventId`, `eventType`, `eventVersion`, `occurredAt`, `runId`, `payload`
- Versioning: `eventVersion` integer; bump on breaking changes
- Delivery: at-least-once; consumers must be idempotent

**State Management Patterns:**
- Server state: TanStack Query only (no custom caches)
- UI state: React local state + context
- Query keys defined in a single module per feature

### Process Patterns

**Error Handling Patterns:**
- API: global exception handler → RFC 7807 Problem Details
- Frontend: app-level ErrorBoundary + per-query errors
- ML: emit `run.failed` event with `errorCode`, `runId`, `eventId`
- User-facing errors: short, actionable; details only in dev

**Loading State Patterns:**
- Frontend: TanStack Query loading states
- List pane: skeletons; detail pane remains stable during list loads
- Run status: global indicator + per-run status in list

**Retry Patterns:**
- Frontend: retry GETs only; no retry for mutations
- API: no automatic retries for writes
- ML: retry idempotent external calls with capped backoff; no retry for pointer swap

**Validation Patterns:**
- API: validate at controller boundary + DB constraints
- ML: validate inputs before writing SQLite; validate event payloads

### Enforcement Guidelines

**All AI Agents MUST:**
- Follow the naming, format, and event envelope rules above.
- Use the designated folders and test locations for each service.
- Emit/consume Redis events with idempotent handling and `eventVersion`.

**Pattern Enforcement:**
- Verify patterns in PR review or checklist before merge.
- Document pattern violations in the PR description and align on fixes.
- Update this section when a pattern intentionally changes.

### Pattern Examples

**Good Examples:**
- API endpoint: `GET /api/runs/{id}`
- JSON: `{ "runId": "r-123", "createdAt": "2026-02-06T14:12:00Z" }`
- Event: `{ "eventType": "run.completed", "eventVersion": 1, "runId": "r-123", "payload": {...} }`
- DB: table `run_items`, column `run_id`, index `idx_run_items__run_id`

**Anti-Patterns:**
- Endpoint: `/api/Run` or `/api/run` (singular/mixed case)
- JSON: `{ "run_id": "r-123" }` (snake_case in API)
- Event: `RunCompleted` or missing `eventVersion`
- DB: `RunItems` table or `runId` column

## Project Structure & Boundaries

### Complete Project Directory Structure
```
jobato/
├── README.md
├── Makefile
├── docker-compose.yml
├── .gitignore
├── .env.example
├── config/
│   ├── api/
│   │   ├── application.yaml
│   │   └── keystore.p12
│   ├── ml/
│   │   └── ml-config.yaml
│   ├── queries.yaml
│   ├── allowlists.yaml
│   └── quota.yaml
├── data/
│   ├── db/
│   │   ├── current-db.txt
│   │   └── runs/
│   └── html/
│       ├── raw/
│       └── canonical/
├── infra/
│   └── redis/
│       └── redis.conf
├── scripts/
│   └── gen-keystore.sh
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── .env
│   ├── .env.example
│   └── src/
│       ├── app/
│       │   ├── App.tsx
│       │   ├── router.tsx
│       │   ├── query-client.ts
│       │   └── providers.tsx
│       ├── features/
│       │   ├── queries/
│       │   │   ├── api/queries-api.ts
│       │   │   ├── components/QueryList.tsx
│       │   │   ├── components/QueryForm.tsx
│       │   │   ├── hooks/use-queries.ts
│       │   │   └── index.ts
│       │   ├── allowlist/
│       │   │   ├── api/allowlist-api.ts
│       │   │   ├── components/AllowlistTable.tsx
│       │   │   ├── hooks/use-allowlist.ts
│       │   │   └── index.ts
│       │   ├── runs/
│       │   │   ├── api/runs-api.ts
│       │   │   ├── components/RunControls.tsx
│       │   │   ├── components/RunStatus.tsx
│       │   │   ├── hooks/use-runs.ts
│       │   │   └── index.ts
│       │   ├── results/
│       │   │   ├── api/results-api.ts
│       │   │   ├── components/ResultsList.tsx
│       │   │   ├── components/ResultDetail.tsx
│       │   │   ├── hooks/use-results.ts
│       │   │   └── index.ts
│       │   ├── feedback/
│       │   │   ├── api/feedback-api.ts
│       │   │   ├── components/FeedbackControls.tsx
│       │   │   ├── hooks/use-feedback.ts
│       │   │   └── index.ts
│       │   └── reports/
│       │       ├── api/reports-api.ts
│       │       ├── components/RunReport.tsx
│       │       ├── hooks/use-reports.ts
│       │       └── index.ts
│       ├── shared/
│       │   ├── ui/
│       │   └── lib/
│       ├── styles/
│       │   └── globals.css
│       ├── types/
│       │   └── api.ts
│       └── assets/
├── api/
│   ├── Dockerfile
│   ├── build.gradle
│   ├── settings.gradle
│   ├── .env
│   ├── .env.example
│   └── src/
│       ├── main/
│       │   ├── java/
│       │   │   └── com/jobato/api/
│       │   │       ├── Application.java
│       │   │       ├── controller/
│       │   │       │   ├── QueryController.java
│       │   │       │   ├── AllowlistController.java
│       │   │       │   ├── RunController.java
│       │   │       │   ├── ResultsController.java
│       │   │       │   ├── FeedbackController.java
│       │   │       │   ├── ReportsController.java
│       │   │       │   └── InternalController.java
│       │   │       ├── service/
│       │   │       │   ├── QueryService.java
│       │   │       │   ├── AllowlistService.java
│       │   │       │   ├── RunService.java
│       │   │       │   ├── ResultService.java
│       │   │       │   ├── FeedbackService.java
│       │   │       │   ├── ReportService.java
│       │   │       │   └── ActiveDbService.java
│       │   │       ├── repository/
│       │   │       │   ├── QueryRepository.java
│       │   │       │   ├── AllowlistRepository.java
│       │   │       │   ├── RunRepository.java
│       │   │       │   ├── ResultRepository.java
│       │   │       │   └── FeedbackRepository.java
│       │   │       ├── model/
│       │   │       │   ├── Run.java
│       │   │       │   ├── ResultItem.java
│       │   │       │   └── FeedbackLabel.java
│       │   │       ├── dto/
│       │   │       │   ├── RunRequest.java
│       │   │       │   ├── RunStatusResponse.java
│       │   │       │   ├── ResultResponse.java
│       │   │       │   └── FeedbackRequest.java
│       │   │       ├── config/
│       │   │       │   ├── WebConfig.java
│       │   │       │   ├── OpenApiConfig.java
│       │   │       │   ├── SecurityConfig.java
│       │   │       │   ├── DataSourceConfig.java
│       │   │       │   └── RedisConfig.java
│       │   │       └── messaging/
│       │   │           └── RunEventsConsumer.java
│       │   └── resources/
│       │       └── db/migration/
│       │           └── V1__init.sql
│       └── test/
│           └── java/com/jobato/api/
│               ├── controller/
│               └── service/
├── ml/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   └── health.py
│   │   ├── pipelines/
│   │   │   ├── run_pipeline.py
│   │   │   ├── ingestion.py
│   │   │   ├── dedupe.py
│   │   │   ├── scoring.py
│   │   │   └── retrain.py
│   │   ├── services/
│   │   │   ├── google_search.py
│   │   │   ├── fetcher.py
│   │   │   ├── cache.py
│   │   │   ├── quota.py
│   │   │   └── pointer_swap.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── models.py
│   │   │   ├── alembic.ini
│   │   │   └── migrations/
│   │   ├── schemas/
│   │   │   ├── events.py
│   │   │   └── results.py
│   │   └── models/
│   └── tests/
│       └── test_run_pipeline.py
```

### Architectural Boundaries

**API Boundaries:**
- Public endpoints:
  - `GET/POST /api/queries`
  - `GET/POST /api/allowlists`
  - `POST /api/runs`
  - `GET /api/runs/{id}`
  - `GET /api/results` (query params for today/all-time)
  - `POST /api/feedback`
  - `GET /api/reports/runs`
  - `GET /api/health`, `GET /api/metrics`
- Internal endpoints (API key):
  - `POST /api/internal/active-db` (pointer swap)
- Data access boundary: API reads/writes only the active SQLite file.

**Component Boundaries:**
- Frontend features are isolated under `frontend/src/features/*`.
- Shared UI components live only in `frontend/src/shared/ui`.
- No direct cross-feature state access; shared state via context providers.

**Service Boundaries:**
- ML publishes `run.*` events to Redis Streams; API consumes.
- API publishes `run.requested` events for ML to consume.
- ML performs pointer swap via internal API call.
- Frontend communicates only with the API.

**Data Boundaries:**
- Config files are mounted from `config/`.
- SQLite files live in `data/db/runs/` and are selected by `data/db/current-db.txt`.
- Raw/canonical HTML stored in `data/html/*` and never in SQLite.
- Redis holds only transient event streams.

### Requirements to Structure Mapping

**Feature/FR Category Mapping:**
- Query and allowlist config (FR1–FR5)
  - Frontend: `frontend/src/features/queries`, `frontend/src/features/allowlist`
  - API: `QueryController`, `AllowlistController`, related services/repos
  - Config: `config/queries.yaml`, `config/allowlists.yaml`
- Run orchestration (FR6–FR10)
  - Frontend: `frontend/src/features/runs`
  - API: `RunController`, `RunService`, `RunEventsConsumer`
  - ML: `ml/app/pipelines/run_pipeline.py`
  - Redis stream: `ml:run-events`
- Ingestion & data capture (FR11–FR18)
  - ML: `ml/app/pipelines/ingestion.py`, `ml/app/services/google_search.py`, `fetcher.py`, `cache.py`
  - Data: `data/html/raw/`, `data/html/canonical/`
- Deduplication (FR19–FR22)
  - ML: `ml/app/pipelines/dedupe.py`, `ml/app/db/models.py`
- Relevance scoring & feedback (FR23–FR27)
  - Frontend: `frontend/src/features/feedback`
  - API: `FeedbackController`, `FeedbackService`
  - ML: `ml/app/pipelines/scoring.py`, `ml/app/pipelines/retrain.py`
- Results review UI (FR28–FR33)
  - Frontend: `frontend/src/features/results`
  - API: `ResultsController`, `ResultService`
- Run reporting/status (FR34–FR37)
  - Frontend: `frontend/src/features/reports`
  - API: `ReportsController`, `ReportService`

**Cross-Cutting Concerns:**
- Quota and caching: `config/quota.yaml` + `ml/app/services/quota.py`
- Observability: API Actuator endpoints; ML metrics in `ml/app/routes/health.py`

### Integration Points

**Internal Communication:**
- Redis Streams event flow:
  - API publishes `run.requested`
  - ML publishes `run.completed` or `run.failed`
- ML calls API to update active DB pointer.

**External Integrations:**
- Google Search API from `ml/app/services/google_search.py`

**Data Flow:**
- User action -> Frontend -> API -> Redis Stream -> ML pipeline
- ML writes new SQLite -> updates pointer -> API reads active DB -> Frontend refreshes results

### File Organization Patterns

**Configuration Files:**
- Shared in `config/`, mounted into containers.
- Service-specific `.env` files live inside each service root.

**Source Organization:**
- Frontend in `frontend/`, API in `api/`, ML in `ml/`.

**Test Organization:**
- Frontend tests co-located, API tests under `api/src/test/java`, ML tests under `ml/tests`.

**Asset Organization:**
- Frontend assets in `frontend/src/assets`, raw data assets under `data/`.

### Development Workflow Integration

**Development Server Structure:**
- `make dev` brings up all services via Docker Compose.
- `make frontend`, `make api`, `make ml` run individual services.

**Build Process Structure:**
- `frontend/` uses Vite build output for production.
- `api/` uses Gradle build.
- `ml/` uses Docker image build with requirements install.

**Deployment Structure:**
- Docker Compose references `config/` and `data/` as shared volumes.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Java Spring API + Python FastAPI + React SPA are compatible with Docker Compose local-first.
- SQLite multi-file model with pointer swap is consistent with ML pipeline and API read/write responsibilities.
- Redis Streams fits ML ↔ API async messaging and idempotency requirements.
- TLS local browser → API and API key for ML → API are consistent with security posture.

**Pattern Consistency:**
- Naming, JSON formats, and error handling patterns align across API, ML, and frontend.
- Event envelope design aligns with Redis Streams and idempotent consumers.
- Feature-based frontend structure aligns with SPA routes and data flows.

**Structure Alignment:**
- Project tree supports service boundaries and shared config/data volumes.
- Integration points (Redis, pointer swap API, shared data) are explicitly mapped.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**
- Query/allowlist configuration, run orchestration, ingestion/capture, dedupe, scoring/feedback, results UI, and reporting all have mapped components and services.

**Non-Functional Requirements Coverage:**
- Performance: SPA caching + list virtualization; API/ML separation.
- Reliability: run status, events, and observable failure states.
- Security: TLS + API key + disk encryption (local-first).
- Accessibility: frontend patterns support WCAG AA; requires implementation follow-through.

### Implementation Readiness Validation ✅

**Decision Completeness:**
- Critical stack decisions and versions documented.
- Messaging, storage, and service boundaries explicit.
- Patterns and examples are concrete and enforceable.

**Structure Completeness:**
- Full repo tree and mappings defined.
- Integration points and boundaries spelled out.

**Pattern Completeness:**
- Naming, format, comms, and process patterns cover all likely conflicts.

### Gap Analysis Results

**Critical Gaps:** None found.

**Important Gaps (optional):**
- Decide whether to enable SQLite WAL mode for better read/write concurrency.
- Specify Redis Streams consumer group names and retry/backoff defaults.

**Nice-to-Have Gaps:**
- E2E test strategy and tooling (deferred).
- CI/CD pipeline definition (already deferred).

### Validation Issues Addressed

- No blocking issues identified. Optional gaps can be deferred without risk.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION  
**Confidence Level:** High

**Key Strengths:**
- Clear boundaries across services with consistent patterns.
- Strong local-first data lifecycle with explicit pointer swap model.
- Concrete repo structure and event contracts.

**Areas for Future Enhancement:**
- Formalize Redis consumer group standards.
- Optional WAL tuning for SQLite.
- Add CI/CD and E2E test strategy.

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented.
- Use implementation patterns consistently across all components.
- Respect project structure and boundaries.
- Refer to this document for all architectural questions.

**First Implementation Priority:**
- Scaffold repo layout + Docker Compose + service templates (Vite React, Spring Boot, FastAPI).

## Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-02-06T01:11:07+0000
**Document Location:** /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/architecture.md

### Final Architecture Deliverables

**📋 Complete Architecture Document**

- All architectural decisions documented with specific versions
- Implementation patterns ensuring AI agent consistency
- Complete project structure with all files and directories
- Requirements to architecture mapping
- Validation confirming coherence and completeness

**🏗️ Implementation Ready Foundation**

- 13 architectural decisions made
- 5 implementation pattern categories defined
- 7 architectural components specified
- 37 requirements fully supported

**📚 AI Agent Implementation Guide**

- Technology stack with verified versions
- Consistency rules that prevent implementation conflicts
- Project structure with clear boundaries
- Integration patterns and communication standards

### Implementation Handoff

**For AI Agents:**
This architecture document is your complete guide for implementing jobato. Follow all decisions, patterns, and structures exactly as documented.

**First Implementation Priority:**
Scaffold repo layout + Docker Compose + service templates (Vite React, Spring Boot, FastAPI).

**Development Sequence:**

1. Initialize project using documented starter template
2. Set up development environment per architecture
3. Implement core architectural foundations
4. Build features following established patterns
5. Maintain consistency with documented rules

### Quality Assurance Checklist

**✅ Architecture Coherence**

- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with all choices

**✅ Requirements Coverage**

- [x] All functional requirements are supported
- [x] All non-functional requirements are addressed
- [x] Cross-cutting concerns are handled
- [x] Integration points are defined

**✅ Implementation Readiness**

- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples are provided for clarity

### Project Success Factors

**🎯 Clear Decision Framework**
Every technology choice was made collaboratively with clear rationale, ensuring all stakeholders understand the architectural direction.

**🔧 Consistency Guarantee**
Implementation patterns and rules ensure that multiple AI agents will produce compatible, consistent code that works together seamlessly.

**📋 Complete Coverage**
All project requirements are architecturally supported, with clear mapping from business needs to technical implementation.

**🏗️ Solid Foundation**
The chosen starter template and architectural patterns provide a production-ready foundation following current best practices.

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin implementation using the architectural decisions and patterns documented herein.

**Document Maintenance:** Update this architecture when major technical decisions are made during implementation.
