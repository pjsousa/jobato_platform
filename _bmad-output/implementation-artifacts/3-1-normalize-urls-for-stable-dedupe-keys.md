# Story 3.1: Normalize URLs for stable dedupe keys

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want results normalized into stable URL keys,
so that the system can reliably detect duplicates.

## Acceptance Criteria

1. **Given** a result URL
   **When** it is ingested
   **Then** a normalized URL key is generated and stored
   **And** the key is used for future dedupe checks

2. **Given** two URLs that differ only by tracking params or casing
   **When** they are normalized
   **Then** they produce the same normalized key
   **And** the raw URL is still preserved

3. **Given** a result URL that cannot be normalized
   **When** normalization fails
   **Then** the system records a clear error
   **And** dedupe is skipped for that item

## Tasks / Subtasks

- [ ] Implement URL normalization logic (AC: 1, 2)
  - [ ] Strip tracking parameters (utm_*, fbclid, gclid, etc.)
  - [ ] Normalize casing (lowercase scheme, host)
  - [ ] Remove default ports
  - [ ] Sort query parameters alphabetically
  - [ ] Remove fragment identifiers
- [ ] Store normalized URL key in database (AC: 1)
  - [ ] Add `normalized_url` column to results table
  - [ ] Create unique constraint on normalized_url for dedupe
  - [ ] Index for fast lookup
- [ ] Handle normalization errors gracefully (AC: 3)
  - [ ] Catch malformed URLs
  - [ ] Log error with original URL
  - [ ] Mark result for manual review
- [ ] Apply normalization in ingestion pipeline (AC: 1)
  - [ ] Normalize before duplicate detection
  - [ ] Link to canonical record when duplicate found
- [ ] Add targeted tests (AC: 1-3)
  - [ ] Unit tests for URL normalization edge cases
  - [ ] Integration tests for dedupe workflow
  - [ ] Error handling tests for malformed URLs

## Dev Notes

### Developer Context

- This story is the foundation for Epic 3's deduplication system (FR19).
- It enables Story 3.2 (duplicate detection) and impacts scoring/relevance (Story 3.3+).
- URL normalization runs in the ML pipeline during result ingestion.
- The normalized key must be deterministic and stable across runs.

### Technical Requirements

- Normalized URL must be a hash-friendly string (SHA-256 recommended for collision resistance).
- Preserve the original URL for display/linking; normalized key is for dedupe only.
- Tracking parameters to strip: `utm_*`, `fbclid`, `gclid`, `msclkid`, `ref`, `source`.
- Malformed URLs should not crash the pipeline; log and continue.
- Normalization must be idempotent: normalize(normalize(url)) == normalize(url).

### Architecture Compliance

- ML pipeline: `ml/app/pipelines/ingestion.py` for normalization during fetch.
- Deduplication: `ml/app/pipelines/dedupe.py` will use normalized keys.
- Database: SQLite via SQLAlchemy; add column via Alembic migration.
- API can read normalized_url for reporting; ML owns writes.
- ML pointer swap model: write to new SQLite, then swap; API reads active DB.

### Library / Framework Requirements

- Python: Use `urllib.parse` for URL parsing (standard library).
- Optional: `url-normalize` package if needed for edge cases.
- SQLAlchemy 2.0.46 for ORM operations.
- Alembic 1.18.3 for schema migrations.

### File Structure Requirements

- ML normalization: `ml/app/pipelines/ingestion.py` (add normalization step).
- ML dedupe: `ml/app/pipelines/dedupe.py` (use normalized keys).
- ML models: `ml/app/db/models.py` (add normalized_url column).
- ML migrations: `ml/app/db/migrations/` (Alembic migration for schema change).
- ML services: `ml/app/services/fetcher.py` (URL validation before normalization).

### Testing Requirements

- ML tests in `ml/tests/test_ingestion.py` for normalization logic.
- ML tests in `ml/tests/test_dedupe.py` for dedupe using normalized keys.
- Edge cases: URLs with unicode, punycode, percent-encoding variations.
- Error cases: empty strings, missing scheme, invalid characters.

### Project Structure Notes

- Keep normalization logic in the ingestion pipeline before storage.
- Deduplication is a separate concern; use normalized keys as input.
- Future stories (3.2+) will add similarity-based dedupe beyond URL matching.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Result Quality Automation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]
- [Source: project-context.md#Critical Implementation Rules]

### Project Context Reference

- Use camelCase for API JSON fields; no snake_case in responses.
- Database columns: snake_case; API responses: camelCase.
- ML must never write to the active SQLite file after pointer swap.
- Use TanStack Query for server data; avoid ad-hoc caches.
- Python: SQLAlchemy/Alembic only for new SQLite files; never write to active DB after pointer swap.

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- _bmad-output/implementation-artifacts/3-1-normalize-urls-for-stable-dedupe-keys.md
