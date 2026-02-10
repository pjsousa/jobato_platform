# Story 3.2: Detect and link duplicates

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want duplicates detected and linked to a canonical result,
so that repeated postings do not clutter review.

## Acceptance Criteria

1. **Given** two results with the same normalized key
   **When** dedupe runs
   **Then** the later result is linked to the canonical record
   **And** the canonical record remains visible by default

2. **Given** two results with high text similarity
   **When** dedupe runs
   **Then** they are linked even if URLs differ
   **And** the duplicate is flagged hidden by default

3. **Given** a duplicate is stored
   **When** it is retrieved via the API
   **Then** it is hidden by default
   **And** its canonical link is available for reference

## Tasks / Subtasks

- [ ] Implement exact URL duplicate detection (AC: 1)
  - [ ] Query by normalized_url to find existing canonical records
  - [ ] Link new duplicates to existing canonical via canonical_id foreign key
  - [ ] Store duplicate count on canonical record
- [ ] Implement text similarity deduplication (AC: 2)
  - [ ] Extract and preprocess visible text from job results
  - [ ] Compute similarity scores (cosine similarity or Jaccard on n-grams)
  - [ ] Define similarity threshold (recommend 0.85-0.90 for job posts)
  - [ ] Link text-similar duplicates to canonical
- [ ] Update database schema for duplicate tracking (AC: 1, 2)
  - [ ] Add canonical_id column to results table (nullable, self-referential FK)
  - [ ] Add duplicate_count column to results table (default 0)
  - [ ] Add is_duplicate boolean column (default false)
  - [ ] Add is_hidden boolean column (default false for canonical, true for duplicates)
  - [ ] Create Alembic migration for schema changes
- [ ] Integrate dedupe into ML ingestion pipeline (AC: 1, 2)
  - [ ] Run dedupe after URL normalization (depends on Story 3.1)
  - [ ] Check exact match first (normalized_url), then text similarity
  - [ ] Process in batch for efficiency during run pipeline
- [ ] API endpoint for duplicate retrieval (AC: 3)
  - [ ] Include canonical record data in duplicate response
  - [ ] Filter hidden duplicates by default in list views
  - [ ] Option to include hidden duplicates in response
- [ ] Add targeted tests (AC: 1-3)
  - [ ] Unit tests for similarity scoring algorithm
  - [ ] Integration tests for duplicate linking workflow
  - [ ] Tests for edge cases (near-threshold similarity, empty text)

## Dev Notes

### Developer Context

- This story builds directly on Story 3.1 (URL normalization) - normalized keys must exist before dedupe runs.
- Part of Epic 3: Result Quality Automation (FR20, FR21, FR22).
- Deduplication happens in the ML pipeline during/after result ingestion.
- Two-phase approach: (1) exact URL match, (2) text similarity for near-duplicates.
- Canonical record is always the FIRST occurrence; later matches are duplicates.
- Hidden duplicates still stored for audit trail and potential un-hiding.

### Technical Requirements

- **URL-based dedupe**: Use normalized_url from Story 3.1 for exact matching.
- **Text similarity**: Use TF-IDF + cosine similarity or similar approach on visible text.
- **Threshold tuning**: Start with 0.90 similarity; make configurable in future.
- **Performance**: Batch process similarities to avoid N^2 comparisons; consider LSH for large datasets.
- **Storage**: Preserve all duplicates; only hide from default view.
- **Idempotency**: Re-running dedupe on same data should produce same results.

### Architecture Compliance

- ML pipeline: `ml/app/pipelines/dedupe.py` - main deduplication logic.
- Integration: Called from `ml/app/pipelines/ingestion.py` after normalization.
- Database: SQLite via SQLAlchemy; schema changes via Alembic migration.
- Models: Update `ml/app/db/models.py` with new columns.
- API: Read-only access to duplicate data; `ResultsController` filters hidden items.
- ML pointer swap: Deduplication writes to new SQLite before pointer swap.

### Library / Framework Requirements

- Python: `scikit-learn` for TF-IDF and cosine similarity (TfidfVectorizer, cosine_similarity).
- Alternative: `numpy` for manual similarity if scikit-learn too heavy.
- SQLAlchemy 2.0.46 for ORM operations.
- Alembic 1.18.3 for schema migrations.

### File Structure Requirements

- ML dedupe logic: `ml/app/pipelines/dedupe.py` (new file or enhance existing).
- ML pipeline integration: `ml/app/pipelines/ingestion.py` (add dedupe step).
- ML models: `ml/app/db/models.py` (add canonical_id, duplicate_count, is_duplicate, is_hidden).
- ML migrations: `ml/app/db/migrations/` (Alembic migration for new columns).
- ML tests: `ml/tests/test_dedupe.py` (new test file).
- API results: `api/src/.../ResultRepository.java` (filter hidden duplicates).

### Testing Requirements

- ML unit tests for similarity algorithm accuracy.
- Integration tests for end-to-end dedupe workflow.
- Edge cases: identical text different URLs, same URL different text, empty content.
- Performance tests for batch processing (simulate 1000+ results).

### Project Structure Notes

- Coordinate with Story 3.1 implementation - ensure normalized_url column exists.
- Deduplication is a pipeline step, not a background service.
- Future enhancement (not in this story): user-visible duplicate grouping UI.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Result Quality Automation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- [Source: _bmad-output/implementation-artifacts/3-1-normalize-urls-for-stable-dedupe-keys.md]
- [Source: project-context.md#Critical Implementation Rules]

### Project Context Reference

- Use camelCase for API JSON fields; no snake_case in responses.
- Database columns: snake_case; API responses: camelCase.
- ML must never write to the active SQLite file after pointer swap.
- Python: SQLAlchemy/Alembic only for new SQLite files; never write to active DB after pointer swap.
- ML event payloads must include eventId, eventType, eventVersion, occurredAt, runId.

### Previous Story Intelligence

From Story 3.1:
- URL normalization runs in `ml/app/pipelines/ingestion.py`.
- Normalized URL stored in `normalized_url` column (hashed/SHA-256 recommended).
- Pattern established: pipeline steps in `ml/app/pipelines/` directory.
- Alembic migrations in `ml/app/db/migrations/`.
- ML tests in `ml/tests/` directory.

### Git Intelligence

Recent commits show pattern:
- ML pipeline development in `ml/app/pipelines/`
- Service logic in `ml/app/services/`
- Database models in `ml/app/db/models.py`

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- _bmad-output/implementation-artifacts/3-2-detect-and-link-duplicates.md
