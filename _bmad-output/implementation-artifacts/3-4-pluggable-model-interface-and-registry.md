# Story 3.4: Pluggable model interface and registry

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a ML developer,
I want the system to load multiple candidate models that follow a scikit-learn style interface,
so that teams can plug in their own models without changing the core pipeline.

## Acceptance Criteria

1. **Given** a model package that implements fit and predict  
   **When** it is registered  
   **Then** the system can load it without code changes to the core pipeline  
   **And** it is available as a selectable candidate

2. **Given** a registry configuration  
   **When** the ML service starts  
   **Then** it discovers all available models  
   **And** exposes their identifiers for evaluation

3. **Given** an invalid model module  
   **When** it is loaded  
   **Then** the system rejects it with a clear error  
   **And** continues with other models

## Tasks / Subtasks

- [ ] Define model interface contract (AC: 1)
  - [ ] Create abstract base class with fit() and predict() methods
  - [ ] Define input/output types for model methods
  - [ ] Document interface requirements for model developers
  - [ ] Create example stub model implementing the interface

- [ ] Implement model registry system (AC: 1, 2)
  - [ ] Create registry configuration schema (YAML-based)
  - [ ] Build registry loader that scans configured model paths
  - [ ] Implement model instantiation from registry entries
  - [ ] Add model metadata tracking (name, version, path, description)
  - [ ] Create singleton registry manager for service lifetime

- [ ] Add model discovery on service startup (AC: 2)
  - [ ] Integrate registry initialization into ML service startup
  - [ ] Add health check endpoint reporting available models
  - [ ] Log discovered models at INFO level
  - [ ] Fail fast if registry config is missing/invalid

- [ ] Implement error handling for invalid models (AC: 3)
  - [ ] Validate model implements required interface methods
  - [ ] Catch import errors and missing dependencies
  - [ ] Log clear error messages with model identifier
  - [ ] Continue loading remaining models after errors
  - [ ] Track failed model attempts for debugging

- [ ] Integrate with existing scoring pipeline (AC: 1)
  - [ ] Refactor scoring.py to use registry instead of hardcoded logic
  - [ ] Add model selection parameter to scoring calls
  - [ ] Maintain backward compatibility (default to baseline if no model specified)
  - [ ] Update ingestion pipeline to pass model identifier

- [ ] Add targeted tests (AC: 1-3)
  - [ ] Unit tests for model interface contract
  - [ ] Tests for registry loading and discovery
  - [ ] Tests for invalid model error handling
  - [ ] Integration tests for end-to-end model registration
  - [ ] Tests for model selection in scoring pipeline

## Dev Notes

### Developer Context

- This story is the foundation for Epic 3's ML model system (FR23-FR25).
- It enables Stories 3.5-3.7 (parallel training, model selection, daily retrain).
- Story 3.3 established baseline scoring (score = 0); this story makes it pluggable.
- The registry pattern allows multiple teams to contribute models without conflicts.
- Models are Python packages that implement a standard scikit-learn style interface.
- The ML service discovers models at startup from a configuration file.

### Technical Requirements

- **Interface Contract**: Abstract base class requiring `fit(X, y)` and `predict(X)` methods.
- **Input/Output Types**: Accept pandas DataFrame or numpy array; return numpy array of scores.
- **Registry Format**: YAML configuration with model identifier, module path, class name, and metadata.
- **Discovery**: Synchronous scan at startup; models loaded into memory for quick selection.
- **Error Isolation**: One failed model must not prevent others from loading.
- **Versioning**: Each model tracks its own version string for selection and comparison.

### Architecture Compliance

- ML pipeline: `ml/app/pipelines/scoring.py` - refactor to use registry.
- ML models directory: `ml/app/models/` - new location for model implementations.
- ML config: `config/ml/models.yaml` - registry configuration file.
- ML registry code: `ml/app/registry/` - new package for registry logic.
- ML service startup: `ml/app/main.py` - integrate registry initialization.
- Health endpoint: `ml/app/routes/health.py` - expose available models.
- ML tests: `ml/tests/test_registry.py`, `ml/tests/test_model_interface.py`.

### Library / Framework Requirements

- Python: `abc` module for abstract base classes (standard library).
- Python: `importlib` for dynamic module loading (standard library).
- Python: PyYAML for registry configuration parsing.
- scikit-learn: Reference interface style (not required as dependency yet).
- SQLAlchemy 2.0.46: Track model versions in database.
- FastAPI: Health endpoint for model discovery reporting.

### File Structure Requirements

- Model interface: `ml/app/registry/model_interface.py` (new file).
- Registry implementation: `ml/app/registry/model_registry.py` (new file).
- Registry config loader: `ml/app/registry/config_loader.py` (new file).
- Example stub model: `ml/app/models/stub_model.py` (new file).
- Registry config: `config/ml/models.yaml` (new file).
- Refactored scoring: `ml/app/pipelines/scoring.py` (modify existing).
- Health endpoint: `ml/app/routes/health.py` (add model list endpoint).
- ML tests: `ml/tests/test_registry.py` (new test file).
- ML tests: `ml/tests/test_model_interface.py` (new test file).

### Testing Requirements

- Unit tests for interface validation (mock models passing/failing contract).
- Unit tests for registry loading from YAML configuration.
- Tests for model discovery and instantiation.
- Error handling tests for invalid/missing models.
- Integration tests for registry + scoring pipeline.
- Health endpoint tests for model listing.

### Project Structure Notes

- Models are plugins; keep them isolated in `ml/app/models/`.
- Registry is a core service; keep in `ml/app/registry/`.
- Configuration is external; use `config/ml/models.yaml`.
- Maintain backward compatibility: scoring pipeline works without registry config (falls back to baseline).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Result Quality Automation]
- [Source: _bmad-output/planning-artifacts/architecture.md#ML/Data Service]
- [Source: _bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md]
- [Source: project-context.md#Critical Implementation Rules]

### Project Context Reference

- Python: SQLAlchemy/Alembic only for new SQLite files; never write to active DB after pointer swap.
- Python: snake_case for modules and functions.
- ML event payloads must include eventId, eventType, eventVersion, occurredAt, runId.
- Use camelCase for API JSON fields; no snake_case in responses.
- Configs are external; do not embed configs in SQLite.

### Previous Story Intelligence

From Story 3.1:
- Pipeline pattern: `ml/app/pipelines/` directory for processing steps.
- Alembic migrations in `ml/app/db/migrations/`.
- ML tests in `ml/tests/` directory.

From Story 3.2:
- Deduplication runs before scoring; canonical results are scored.
- Database schema additions follow established pattern (add column, create migration, update model).

From Story 3.3:
- Scoring pipeline located at `ml/app/pipelines/scoring.py`.
- Baseline model returns score 0 for all results.
- Score storage includes relevance_score, scored_at, score_version columns.
- Scoring happens during ingestion pipeline after deduplication.
- ML pipeline processes results in batch during run pipeline.

**Key Learnings:**
- Pipeline steps are modular and composable.
- Database schema changes require Alembic migrations.
- Tests are co-located with code in `ml/tests/`.
- ML service uses FastAPI with clear route separation.

### Git Intelligence

Recent commits show pattern:
- ML pipeline development in `ml/app/pipelines/`
- Database schema changes via Alembic migrations
- Co-located tests for each pipeline component
- Feature-based organization in ML service

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- _bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md
