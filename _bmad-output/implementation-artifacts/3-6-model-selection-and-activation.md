---
epic: 3
story: 6
title: Model selection and activation
status: ready-for-dev
---

# Story 3.6: Model selection and activation

Status: ready-for-dev

## Story

As a user,
I want to view candidate metrics and promote one model to active use,
So that scoring uses the best available model.

## Acceptance Criteria

**AC 1: View candidate evaluation metrics**

**Given** evaluation results exist
**When** I request comparisons
**Then** I can see each candidate's metrics for the run
**And** results are grouped by model version

**AC 2: Promote candidate to active model**

**Given** a candidate is promoted
**When** new results are scored
**Then** the active model is used
**And** its version is recorded with each score

**AC 3: Model rollback capability**

**Given** a previous model is selected again
**When** I switch back
**Then** the system can roll back to that model version
**And** scoring resumes with the selected version

## Tasks / Subtasks

- [ ] Task 1: Create model selection API endpoints (AC: #1, #2)
  - [ ] GET /api/ml/models - List all registered models with their status
  - [ ] GET /api/ml/models/comparisons - Get evaluation metrics for all candidates
  - [ ] POST /api/ml/models/{id}/activate - Promote model to active status
  - [ ] GET /api/ml/models/active - Get currently active model details
  
- [ ] Task 2: Implement model activation service (AC: #2)
  - [ ] Create activation logic that updates active model pointer
  - [ ] Validate model exists and has valid evaluation metrics before activation
  - [ ] Store activation history with timestamps
  - [ ] Emit model.activated event to Redis
  
- [ ] Task 3: Build model comparison UI (AC: #1)
  - [ ] Create model comparison table with metrics (precision, recall, F1, accuracy)
  - [ ] Show model version and evaluation timestamp
  - [ ] Highlight currently active model
  - [ ] Add visual indicators for best performing metrics
  
- [ ] Task 4: Implement model activation UI (AC: #2, #3)
  - [ ] Add "Activate" button for each candidate model
  - [ ] Create confirmation modal with model details
  - [ ] Show activation success/error feedback
  - [ ] Display activation history/rollback options
  
- [ ] Task 5: Create active model persistence (AC: #2, #3)
  - [ ] Store active model reference in SQLite (config table or dedicated table)
  - [ ] Ensure atomic updates to prevent race conditions
  - [ ] Maintain model activation history log
  - [ ] Link active model to scoring pipeline
  
- [ ] Task 6: Integrate with scoring pipeline (AC: #2)
  - [ ] Update scoring pipeline to load active model dynamically
  - [ ] Record active model version with each score
  - [ ] Handle case where no active model exists (use default score 0)
  - [ ] Add fallback logic for missing/deleted models
  
- [ ] Task 7: Implement rollback functionality (AC: #3)
  - [ ] Show list of previously active models from history
  - [ ] Allow re-activation of previous model versions
  - [ ] Validate rollback target exists and is loadable
  - [ ] Emit model.rollback event when rollback occurs
  
- [ ] Task 8: Testing (AC: #1, #2, #3)
  - [ ] Unit tests for model activation service
  - [ ] Unit tests for comparison metrics aggregation
  - [ ] Integration tests for full activation flow
  - [ ] E2E tests for model selection UI workflow

## Dev Notes

### Context from Previous Stories (3.1-3.5)

From Story 3.5 (Parallel evaluation), we established:
- Evaluation results are stored with metrics (precision, recall, F1, accuracy)
- Each evaluation ties to a model version and dataset
- Worker pool processes evaluations concurrently
- Metrics schema supports extensibility

From Story 3.4 (Pluggable model interface), we established:
- Models implement `fit(X, y)` and `predict(X)` interface
- Model registry discovers models dynamically from `ml/app/models/`
- Model identifiers follow pattern: `{model_name}:{version}`
- Model metadata includes author, description, creation date

From Story 3.3 (Baseline scoring), we established:
- Scores range from -1 to 1
- Default score is 0 when no active model exists
- Model versioning is required for tracking
- Scoring pipeline must record which model version produced each score

From Stories 3.1-3.2 (Deduplication), we have:
- Normalized URL keys for deduplication
- Canonical record linking
- Post-processing pipeline structure

### Architecture Compliance

**ML Service Structure:**
- Model selector service: `ml/app/services/model_selector.py` (new file)
- Activation logic: `ml/app/services/model_activation.py` (new file)
- Active model store: Extend `ml/app/db/models.py` with ActiveModel table
- Comparison API: `ml/app/routes/models.py` (new file)

**API Service Structure:**
- Proxy endpoints: `api/src/.../controller/MlModelController.java` (new file)
- Internal client: `api/src/.../service/MlModelClient.java` (new file)
- DTOs: `api/src/.../dto/ModelComparisonResponse.java`, `ModelActivationRequest.java`

**Frontend Structure:**
- Feature folder: `frontend/src/features/models/` (new)
  - `api/models-api.ts` - API client
  - `components/ModelComparisonTable.tsx` - Comparison UI
  - `components/ModelActivationButton.tsx` - Activation controls
  - `components/ModelHistoryList.tsx` - Rollback UI
  - `hooks/use-models.ts` - Data fetching

**Data Architecture:**
- Active model stored in SQLite config table or dedicated table
- Model activation history tracked for rollback
- Evaluation results reference model by ID and version
- Atomic pointer swap pattern for activation (similar to DB pointer swap)

**Event Patterns:**
- Stream: `ml:run-events`
- Event types:
  - `model.activated` - When model is promoted to active
  - `model.rollback` - When reverting to previous model
  - `model.deactivated` - When active model is replaced
- Envelope: `{eventId, eventType, eventVersion: 1, occurredAt, runId, payload: {modelId, version, previousModelId}}`

**API Patterns:**
- ML service exposes internal endpoints (not public API)
- API service proxies/aggregates for frontend
- Use RFC 7807 error responses for validation failures

### Technical Requirements

**Data Models:**

```python
# ActiveModel (new table)
{
  "id": "uuid",
  "modelId": "string",          # e.g., "random_forest"
  "version": "string",          # e.g., "v1.2.3"
  "activatedAt": "timestamp",
  "activatedBy": "string",      # user or system
  "evaluationId": "uuid",       # reference to evaluation that justified activation
  "isActive": "boolean"         # true for current active model
}

# ModelActivationHistory (new table)
{
  "id": "uuid",
  "modelId": "string",
  "version": "string",
  "action": "enum[activated, deactivated, rollback]",
  "timestamp": "timestamp",
  "previousModelId": "string?",  # for rollback tracking
  "reason": "string?"            # optional activation reason
}
```

**API Endpoints:**

```
# ML Service (Internal)
GET    /ml/models                    # List all registered models
GET    /ml/models/comparisons        # Get evaluation metrics comparison
POST   /ml/models/{id}/activate      # Activate specific model
GET    /ml/models/active             # Get currently active model
POST   /ml/models/{id}/rollback      # Rollback to previous version

# API Service (Public)
GET    /api/ml/models                # Proxy to ML service
GET    /api/ml/models/comparisons    # Proxy to ML service
POST   /api/ml/models/{id}/activate  # Proxy to ML service
GET    /api/ml/models/active         # Proxy to ML service
GET    /api/ml/models/history        # Get activation history
```

**Configuration:**
- Default model: string (model ID to use if no active model set)
- AllowRollback: boolean (default: true)
- MaxHistoryEntries: int (default: 50)

### Project Structure Notes

**New Files to Create:**
```
ml/
├── app/
│   ├── services/
│   │   ├── model_selector.py      # Model comparison logic
│   │   └── model_activation.py    # Activation/rollback logic
│   ├── routes/
│   │   └── models.py              # Model management endpoints
│   └── db/
│       └── models.py              # Add ActiveModel, ModelActivationHistory

api/
└── src/...
    ├── controller/
    │   └── MlModelController.java
    ├── service/
    │   └── MlModelClient.java
    └── dto/
        ├── ModelComparisonResponse.java
        ├── ModelActivationRequest.java
        └── ModelHistoryResponse.java

frontend/
└── src/
    └── features/
        └── models/
            ├── api/
            │   └── models-api.ts
            ├── components/
            │   ├── ModelComparisonTable.tsx
            │   ├── ModelActivationButton.tsx
            │   ├── ModelHistoryList.tsx
            │   └── ModelMetricsCard.tsx
            ├── hooks/
            │   └── use-models.ts
            └── index.ts
```

**Database Migrations:**
- Add `active_models` table
- Add `model_activation_history` table
- Add index on `active_models.isActive` for quick lookup

### Integration Points

**Input:**
- Model registry (from Story 3.4) - list of available models
- Evaluation results (from Story 3.5) - metrics for comparison
- User feedback labels - for ground truth validation

**Output:**
- Active model reference - used by scoring pipeline
- Activation events - for audit and monitoring
- Model version recorded with each score

**Dependencies:**
- Story 3.4 (Model registry) must be completed
- Story 3.5 (Evaluation) should have results to compare
- Story 3.3 (Scoring) must integrate with active model

### Critical Implementation Notes

1. **Atomic Activation:** Model activation must be atomic - use transaction or pointer swap pattern to prevent partial activation states

2. **Validation Before Activation:**
   - Verify model exists in registry
   - Verify model has evaluation results
   - Verify model is loadable (try import before activation)
   - Warn if metrics are stale (> 7 days old)

3. **Scoring Pipeline Integration:**
   - Scoring must check active model on each run
   - Cache active model reference but refresh periodically
   - Fall back to default score (0) if active model fails to load

4. **Rollback Safety:**
   - Keep model files for all versions in activation history
   - Validate rollback target before switching
   - Maintain at least one backup model (previous active)

5. **History Management:**
   - Prune old history entries beyond MaxHistoryEntries
   - Never delete history for currently active model
   - Include reason codes for activations (user, scheduled, rollback)

6. **UI/UX Considerations:**
   - Show loading state during model switch
   - Display confirmation for rollback actions
   - Highlight significant metric differences (> 5%)
   - Show "last evaluated" timestamp to indicate data freshness

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.6]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns]
- [Source: _bmad-output/implementation-artifacts/3-5-parallel-candidate-training-and-evaluation.md] - Evaluation results structure
- [Source: _bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md] - Model registry interface
- [Source: _bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md] - Scoring integration

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

*Ultimate context engine analysis completed - comprehensive developer guide created*
