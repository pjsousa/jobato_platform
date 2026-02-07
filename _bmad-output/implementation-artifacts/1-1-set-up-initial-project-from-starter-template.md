# Story 1.1: Set up initial project from starter template

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to initialize the project from the approved starter templates,
so that the system can run locally with baseline services.

## Acceptance Criteria

1. Given the approved starter templates (Vite React TypeScript, Spring Boot, FastAPI), when I initialize the project, then service skeletons are created under frontend/, api/, and ml/ and the repository includes infra/, config/, data/, and scripts/ folders.
2. Given docker-compose is started, when services are running, then API and ML health endpoints respond and Redis is reachable by both services.
3. Given shared volumes are configured, when services run, then config/ and data/ are mounted and each service includes a .env.example file.
4. Given the baseline is up, when I verify runtime behavior, then only health checks are required and no business logic is required for this story.
5. Given the service skeletons exist, when I run each service build command, then frontend, API, and ML builds complete successfully and build artifacts are generated in their default locations.
6. Given dependencies are installed and configs are generated, when I start services via docker-compose, then all services start without errors and health endpoints return HTTP 200.

## Tasks / Subtasks

- [ ] Scaffold repo layout and shared folders (AC: 1, 3)
  - [ ] Create top-level folders: frontend/, api/, ml/, infra/, config/, data/, scripts/
  - [ ] Add baseline config/ and data/ subfolders (data/db/runs, data/db/current-db.txt, data/html/raw, data/html/canonical) and keep data/ gitignored
  - [ ] Add .env.example in frontend/, api/, ml/ (and root .env.example if used)
- [ ] Initialize service skeletons with starter templates (AC: 1, 5)
  - [ ] Frontend: Vite React TS in frontend/
  - [ ] API: Spring Boot Java 17 Gradle in api/ with web, validation, data-jdbc, actuator, springdoc
  - [ ] ML: FastAPI scaffold in ml/ with requirements.txt and basic app entry
- [ ] Docker Compose baseline with Redis and shared volumes (AC: 2, 3, 6)
  - [ ] docker-compose.yml brings up frontend, api, ml, redis; mounts config/ and data/ into api and ml
  - [ ] Ensure Redis is reachable from api and ml via service hostname
  - [ ] Add health endpoints: API via Actuator, ML via FastAPI route
- [ ] Build and runtime checks (AC: 4, 5, 6)
  - [ ] Frontend, API, and ML build commands succeed
  - [ ] docker-compose up starts all services; health endpoints return HTTP 200

## Dev Notes

### Developer Context

- This story is scaffold-only: no business logic beyond basic health endpoints.
- Follow the approved multi-service baseline and keep service boundaries strict (frontend/api/ml).

### Technical Requirements

- Use the pinned stack versions: React Router 7.13.0, TanStack Query 5.90.20, react-window 2.2.6, Spring Boot 4.0.2.RELEASE (Java 17), SpringDoc 3.0.1, Flyway 12.0.0, FastAPI, SQLAlchemy 2.0.46, Alembic 1.18.3, Redis 8.4, SQLite 3.51.2.
- API conventions: REST + JSON under /api, RFC 7807 Problem Details for errors; expose /api/health and /api/metrics via Actuator.
- ML service must expose a basic health endpoint (HTTP 200) for docker-compose checks.

### Architecture Compliance

- Docker Compose is the local-first baseline; services must mount shared config/ and data/ volumes.
- Data layout is required from day one: data/db/current-db.txt and data/db/runs/ plus data/html/raw and data/html/canonical; raw/canonical HTML must never be stored in SQLite.
- Internal API endpoints must require X-Jobato-Api-Key; add env placeholders now even if not fully wired.
- Configs live in config/ and per-service .env files; do not embed configs in code or SQLite.

### Library and Framework Requirements

- Frontend scaffold: `npm create vite@latest` with the react-ts template in frontend/. Vite current homepage lists v7.3.1; keep to architecture-approved versions and lock dependencies.
- API scaffold: Spring Initializr with bootVersion 4.0.2.RELEASE, Java 17, Gradle, dependencies web, validation, data-jdbc, actuator; add SpringDoc 3.0.1 and Micrometer 1.16.2.
- ML scaffold: Python 3 with `pip install "fastapi[standard]"`; use FastAPI CLI (`fastapi dev`) for local health checks.
- Redis container: Redis 8.4 for Streams; reachable by api and ml via docker-compose service name.

### Testing and Verification Requirements

- Frontend: `npm run build` succeeds in frontend/.
- API: `./gradlew build` succeeds in api/.
- ML: install requirements and ensure the app boots; run a minimal import check or `fastapi dev` for health route.
- docker-compose up starts all services; /api/health and ML /health return HTTP 200; Redis accepts a connection from api and ml.

### Latest Technical Notes

- Vite homepage lists v7.3.1; use `npm create vite@latest` and lock versions per architecture (do not upgrade React Router or TanStack Query versions).
- Spring Boot project page lists 4.0.2; keep bootVersion 4.0.2.RELEASE as specified in architecture.
- FastAPI docs recommend `pip install "fastapi[standard]"` and `fastapi dev` for local run.

### Project Context Reference

- Follow the AI agent rules in project context for stack versions, naming conventions, and data handling.

### Project Structure Notes

- Align with the unified repo layout: root docker-compose.yml, Makefile, .env.example; top-level frontend/, api/, ml/, infra/, config/, data/, scripts/.
- Keep service internal structure consistent with architecture (frontend/src/app + features + shared; api package com.jobato.api; ml/app + pipelines + services + db + schemas).
- No conflicts detected for this story; do not introduce alternate layouts or shared cross-service code.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Starter Template Evaluation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/project-context.md#Technology Stack & Versions]

## Dev Agent Record

### Agent Model Used

openai/gpt-5.2-codex

### Debug Log References

- Validation workflow file not found: _bmad/core/tasks/validate-workflow.xml

### Completion Notes List

- Story drafted from epics, architecture, PRD, UX, and project-context.
- Web research performed for Vite, Spring Boot, and FastAPI current guidance.

### File List

- _bmad-output/implementation-artifacts/1-1-set-up-initial-project-from-starter-template.md
