# Story 3.3: Assign relevance scores (baseline)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want each result assigned a relevance score,
so that review is prioritized by likely fit.

## Acceptance Criteria

1. **Given** a new result
   **When** it is scored
   **Then** it receives a score in the range -1 to 1
   **And** the score is stored with the result

2. **Given** no prior model exists
   **When** a result is scored
   **Then** the default score is 0
   **And** the scoring pipeline completes successfully

3. **Given** a stored score
   **When** results are retrieved
   **Then** the score is available for sorting and display
   **And** the API returns it in the response payload

## Tasks / Subtasks

- [ ] Implement baseline scoring logic (AC: 1, 2)
  - [ ] Create scoring pipeline that assigns default score of 0
  - [ ] Ensure score is within valid range (-1 to 1)
  - [ ] Store score with timestamp and version
- [ ] Update database schema for score storage (AC: 1, 3)
  - [ ] Add `relevance_score` column to results table (float, -1 to 1)
  - [ ] Add `scored_at` timestamp column
  - [ ] Add `score_version` column for model versioning (default "baseline")
  - [ ] Create Alembic migration for schema changes
- [ ] Integrate scoring into ML pipeline (AC: 1, 2)
  - [ ] Add scoring step after deduplication in ingestion pipeline
  - [ ] Score all new results (non-duplicates) with default 0
  - [ ] Skip scoring for duplicates (they inherit from canonical)
- [ ] API endpoint updates for score retrieval (AC: 3)
  - [ ] Include relevance_score in result response payload
  - [ ] Support sorting by relevance_score in results list
  - [ ] Return score metadata (scored_at, score_version)
- [ ] Add targeted tests (AC: 1-3)
  - [ ] Unit tests for scoring pipeline
  - [ ] Integration tests for score storage and retrieval
  - [ ] Tests for score range validation
  - [ ] Tests for duplicate inheritance behavior

## Dev Notes

### Developer Context

- This story establishes the baseline scoring system for Epic 3 (FR23, FR24).
- It builds on Story 3.2 (deduplication) - canonical results are scored; duplicates inherit scores.
- The baseline model (score = 0) is a placeholder for future ML models (Stories 3.4-3.7).
- Scoring happens in the ML pipeline during result ingestion, after deduplication.
- Score range -1 (irrelevant) to 1 (highly relevant), with 0 as neutral/default.

### Technical Requirements

- **Scoring Logic**: Default all results to score 0.0 (baseline model).
- **Score Storage**: Float value in SQLite; constraint check for range -1.0 to 1.0.
- **Score Metadata**: Track when scored (`scored_at`) and by which model version (`score_version`).
- **Duplicate Handling**: Duplicates (linked via `canonical_id` from Story 3.2) do not get separate scores; they display the canonical's score.
- **API Contract**: Scores returned as floats in camelCase (`relevanceScore`, `scoredAt`, `scoreVersion`).
- **Sorting**: Results sorted by `relevance_score DESC` as secondary sort after `first_seen DESC`.

### Architecture Compliance

- ML pipeline: `ml/app/pipelines/scoring.py` - new pipeline step for scoring.
- Integration: Called from `ml/app/pipelines/ingestion.py` after deduplication step.
- Database: SQLite via SQLAlchemy; schema changes via Alembic migration.
- Models: Update `ml/app/db/models.py` with new columns (`relevance_score`, `scored_at`, `score_version`).
- API: `ResultsController` returns scores; `ResultService` handles sorting.
- ML pointer swap: Scoring writes to new SQLite before pointer swap.

### Library / Framework Requirements

- Python: Standard library only for baseline scoring (no ML libraries needed yet).
- SQLAlchemy 2.0.46 for ORM operations.
- Alembic 1.18.3 for schema migrations.
- FastAPI for API endpoints (already in ML service scaffold).

### File Structure Requirements

- ML scoring logic: `ml/app/pipelines/scoring.py` (new file).
- ML pipeline integration: `ml/app/pipelines/ingestion.py` (add scoring step after dedupe).
- ML models: `ml/app/db/models.py` (add relevance_score, scored_at, score_version columns).
- ML migrations: `ml/app/db/migrations/` (Alembic migration for new columns).
- ML tests: `ml/tests/test_scoring.py` (new test file).
- API results: `api/src/.../ResultResponse.java` (add relevanceScore field).

### Testing Requirements

- ML unit tests for scoring pipeline logic.
- Integration tests for end-to-end scoring workflow.
- Edge cases: boundary values (-1, 0, 1), null handling, duplicate inheritance.
- API tests for score retrieval and sorting.

### Project Structure Notes

- Coordinate with Story 3.2 implementation - ensure deduplication runs before scoring.
- Scoring is a pipeline step, not a background service.
- Future enhancement (Stories 3.4-3.7): Replace baseline with actual ML model scoring.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Result Quality Automation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/prd.md#FR23-FR25]
- [Source: _bmad-output/implementation-artifacts/3-2-detect-and-link-duplicates.md]
- [Source: project-context.md#Critical Implementation Rules]

### Project Context Reference

- Use camelCase for API JSON fields; no snake_case in responses.
- Database columns: snake_case; API responses: camelCase.
- ML must never write to the active SQLite file after pointer swap.
- Python: SQLAlchemy/Alembic only for new SQLite files; never write to active DB after pointer swap.
- ML event payloads must include eventId, eventType, eventVersion, occurredAt, runId.

### Previous Story Intelligence

From Story 3.1:
- Pipeline pattern: `ml/app/pipelines/` directory for processing steps.
- Alembic migrations in `ml/app/db/migrations/`.
- ML tests in `ml/tests/` directory.

From Story 3.2:
- Deduplication runs before scoring; duplicates linked via `canonical_id`.
- Canonical records are the source of truth; duplicates inherit properties.
- Database schema additions follow established pattern (add column, create migration, update model).
- Pattern: pipeline steps process results in batch during run pipeline.

### Git Intelligence

Recent commits show pattern:
- ML pipeline development in `ml/app/pipelines/`
- Database schema changes via Alembic migrations
- API response updates in DTO classes
- Co-located tests for each pipeline component

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- _bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md
