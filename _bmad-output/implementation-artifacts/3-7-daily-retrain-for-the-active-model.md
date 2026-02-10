---
epic: 3
story: 7
title: Daily retrain for the active model
status: ready-for-dev
---

# Story 3.7: Daily retrain for the active model

Status: ready-for-dev

## Story

As a user,
I want the active model retrained daily,
So that feedback improves tomorrow's results.

## Acceptance Criteria

**AC 1: Daily retrain job execution**

**Given** labeled results exist
**When** the daily retrain job runs
**Then** the active model is retrained and a new version is produced
**And** the model version is recorded for the run

**AC 2: Retrained model usage**

**Given** the daily retrain completes
**When** new results are scored
**Then** the latest active model version is used
**And** the version is stored with each score

**AC 3: No new labels handling**

**Given** no new labels exist
**When** the retrain job runs
**Then** the system completes without error
**And** retains the current active model version

## Tasks / Subtasks

- [ ] Task 1: Create daily retrain scheduler (AC: #1)
  - [ ] Implement scheduler service in ML service
  - [ ] Configure daily schedule (default: 06:00 local time)
  - [ ] Add manual trigger endpoint for immediate retrain
  - [ ] Add configuration for retrain time and enabled/disabled state
  
- [ ] Task 2: Implement retrain pipeline (AC: #1)
  - [ ] Load all labeled results since last retrain
  - [ ] Prepare training dataset from labels
  - [ ] Retrain the currently active model with new data
  - [ ] Generate new model version with timestamp suffix
  - [ ] Save retrained model to `ml/app/models/trained/`
  
- [ ] Task 3: Model validation and promotion (AC: #1, #2)
  - [ ] Validate retrained model loads correctly
  - [ ] Run quick validation on holdout set
  - [ ] Auto-promote to active if validation passes
  - [ ] Emit `model.retrained` event with version info
  
- [ ] Task 4: Update scoring pipeline integration (AC: #2)
  - [ ] Ensure scoring pipeline loads latest active model version
  - [ ] Record model version with each score
  - [ ] Handle case where retrain is in progress during scoring
  
- [ ] Task 5: Create retrain job API endpoints (AC: #1)
  - [ ] GET /api/ml/retrain/status - Get last retrain status
  - [ ] POST /api/ml/retrain/trigger - Manual retrain trigger
  - [ ] GET /api/ml/retrain/history - List retrain history
  
- [ ] Task 6: Build retrain status UI (AC: #1)
  - [ ] Show last retrain timestamp and status
  - [ ] Display retrain history with metrics
  - [ ] Add manual "Retrain Now" button
  - [ ] Show next scheduled retrain time
  
- [ ] Task 7: Handle edge cases (AC: #3)
  - [ ] Skip retrain when no new labels since last run
  - [ ] Handle retrain failure gracefully (keep previous model)
  - [ ] Implement maximum retrain duration timeout
  - [ ] Add retry logic for transient failures
  
- [ ] Task 8: Testing (AC: #1, #2, #3)
  - [ ] Unit tests for retrain pipeline
  - [ ] Unit tests for scheduler service
  - [ ] Integration tests for full retrain flow
  - [ ] Test edge case: no new labels

## Dev Notes

### Context from Previous Stories (3.1-3.6)

From Story 3.6 (Model selection and activation), we established:
- Active model is stored in SQLite with `isActive` flag
- Model activation history tracks all activation events
- Models have identifiers like `{model_name}:{version}`
- Activation is atomic using pointer swap pattern
- Events: `model.activated`, `model.rollback`, `model.deactivated`

From Story 3.5 (Parallel evaluation), we established:
- Evaluation results stored with metrics (precision, recall, F1, accuracy)
- Metrics tied to model version and dataset
- Model versions follow semantic versioning pattern

From Story 3.4 (Pluggable model interface), we established:
- Models implement `fit(X, y)` and `predict(X)` interface
- Model registry discovers models from `ml/app/models/`
- Trained models stored separately from registered model code

From Story 3.3 (Baseline scoring), we established:
- Scores range from -1 to 1
- Model version recorded with each score
- Default score 0 when no model exists

### Architecture Compliance

**ML Service Structure:**
- Retrain scheduler: `ml/app/services/retrain_scheduler.py` (new file)
- Retrain pipeline: `ml/app/pipelines/retrain.py` (extend existing)
- Model versioning: `ml/app/services/model_versioning.py` (new file)
- Retrain API: `ml/app/routes/retrain.py` (new file)

**API Service Structure:**
- Proxy endpoints: `api/src/.../controller/RetrainController.java` (new file)
- Internal client: `api/src/.../service/RetrainClient.java` (new file)
- DTOs: `api/src/.../dto/RetrainStatusResponse.java`, `RetrainTriggerRequest.java`

**Frontend Structure:**
- Feature folder: `frontend/src/features/retrain/` (new)
  - `api/retrain-api.ts` - API client
  - `components/RetrainStatusCard.tsx` - Status display
  - `components/RetrainHistoryTable.tsx` - History UI
  - `components/RetrainTriggerButton.tsx` - Manual trigger
  - `hooks/use-retrain.ts` - Data fetching

**Data Architecture:**
- Retrain history stored in SQLite (new table)
- Model files stored in `data/models/` or `ml/app/models/trained/`
- Each retrain creates new model file, old versions retained for rollback
- Active model reference updated after successful retrain

**Event Patterns:**
- Stream: `ml:run-events`
- Event types:
  - `model.retrain.started` - When retrain job begins
  - `model.retrain.completed` - When retrain succeeds
  - `model.retrain.failed` - When retrain fails
  - `model.promoted` - When retrained model becomes active
- Envelope: `{eventId, eventType, eventVersion: 1, occurredAt, runId, payload: {modelId, previousVersion, newVersion, metrics}}`

**API Patterns:**
- ML service exposes internal endpoints
- API service proxies for frontend
- Use RFC 7807 error responses

### Technical Requirements

**Data Models:**

```python
# RetrainJob (new table)
{
  "id": "uuid",
  "modelId": "string",           # Model being retrained
  "previousVersion": "string",   # Version before retrain
  "newVersion": "string",        # Version after retrain
  "status": "enum[pending, running, completed, failed, skipped]",
  "startedAt": "timestamp",
  "completedAt": "timestamp?",
  "labelCount": "int",           # Number of labels used
  "metrics": {                   # Post-retrain validation metrics
    "precision": "float",
    "recall": "float",
    "f1": "float",
    "accuracy": "float"
  },
  "errorMessage": "string?"      # If failed
}

# RetrainConfig (new table or config file)
{
  "schedule": "cron expression",  # Default: "0 6 * * *" (6 AM daily)
  "enabled": "boolean",           # Default: true
  "timeoutMinutes": "int",        # Default: 30
  "minLabelsRequired": "int",     # Default: 5
  "autoPromote": "boolean"        # Default: true
}
```

**API Endpoints:**

```
# ML Service (Internal)
GET    /ml/retrain/status          # Get current/last retrain status
POST   /ml/retrain/trigger         # Trigger manual retrain
GET    /ml/retrain/history         # List retrain history
GET    /ml/retrain/config          # Get retrain configuration
PUT    /ml/retrain/config          # Update retrain configuration

# API Service (Public)
GET    /api/ml/retrain/status      # Proxy to ML service
POST   /api/ml/retrain/trigger     # Proxy to ML service
GET    /api/ml/retrain/history     # Proxy to ML service
GET    /api/ml/retrain/config      # Proxy to ML service
PUT    /api/ml/retrain/config      # Proxy to ML service
```

**Configuration:**
- `RETRAIN_SCHEDULE`: Cron expression (default: "0 6 * * *")
- `RETRAIN_ENABLED`: boolean (default: true)
- `RETRAIN_TIMEOUT_MINUTES`: int (default: 30)
- `RETRAIN_MIN_LABELS`: int (default: 5)
- `RETRAIN_AUTO_PROMOTE`: boolean (default: true)

### Project Structure Notes

**New Files to Create:**
```
ml/
├── app/
│   ├── services/
│   │   ├── retrain_scheduler.py    # APScheduler or similar
│   │   └── model_versioning.py     # Version generation logic
│   ├── pipelines/
│   │   └── retrain.py              # Extend with full retrain flow
│   ├── routes/
│   │   └── retrain.py              # Retrain management endpoints
│   └── db/
│       └── models.py               # Add RetrainJob, RetrainConfig

api/
└── src/...
    ├── controller/
    │   └── RetrainController.java
    ├── service/
    │   └── RetrainClient.java
    └── dto/
        ├── RetrainStatusResponse.java
        ├── RetrainTriggerRequest.java
        └── RetrainHistoryResponse.java

frontend/
└── src/
    └── features/
        └── retrain/
            ├── api/
            │   └── retrain-api.ts
            ├── components/
            │   ├── RetrainStatusCard.tsx
            │   ├── RetrainHistoryTable.tsx
            │   ├── RetrainTriggerButton.tsx
            │   └── RetrainConfigForm.tsx
            ├── hooks/
            │   └── use-retrain.ts
            └── index.ts
```

**Database Migrations:**
- Add `retrain_jobs` table
- Add `retrain_config` table (or use existing config mechanism)
- Add index on `retrain_jobs.startedAt` for history queries

### Integration Points

**Input:**
- Feedback labels from API/database
- Active model reference from Story 3.6
- Model registry from Story 3.4
- Previous retrain job status

**Output:**
- New model version file
- Updated active model reference
- Retrain events for monitoring
- Model version recorded with scores

**Dependencies:**
- Story 3.4 (Model registry) - for model interface
- Story 3.6 (Model activation) - for promotion logic
- Story 4.4 (Mark job as irrelevant) - for label data

**Data Flow:**
1. Scheduler triggers retrain job
2. Load all labels since last retrain
3. If labels < minLabelsRequired, skip with `skipped` status
4. Load active model and call `fit(X, y)` with new labels
5. Generate new version (e.g., append timestamp)
6. Save model file to `ml/app/models/trained/{model_id}_{version}.pkl`
7. Run validation on holdout set
8. If autoPromote=true and validation passes:
   - Update active model reference
   - Emit `model.promoted` event
9. Record retrain job completion
10. If failed, emit `model.retrain.failed` and keep previous model

### Critical Implementation Notes

1. **Retrain Scheduling:**
   - Use APScheduler or similar for cron-based scheduling
   - Ensure only one retrain job runs at a time
   - Allow manual trigger to override scheduled job
   - Handle timezone properly (default to system local time)

2. **Model Versioning:**
   - Format: `{base_version}-{timestamp}` (e.g., "v1.2.3-20260209060000")
   - Store version metadata with model file
   - Maintain link between retrain job and model version

3. **Label Collection:**
   - Query labels from `feedback_labels` table
   - Filter for labels since `lastRetrainAt`
   - Include both "relevant" and "irrelevant" labels
   - Transform to training format expected by model

4. **Validation Before Promotion:**
   - Use stratified split for holdout validation
   - Minimum metrics thresholds (configurable)
   - If validation fails, mark retrain as failed but keep model file for inspection
   - Alert on significant metric degradation

5. **Scoring Pipeline Integration:**
   - Scoring must detect when active model version changes
   - Cache model in memory but check version periodically
   - Handle case where scoring starts during retrain (use previous model)

6. **Error Handling:**
   - Transient failures: retry up to 3 times with backoff
   - Permanent failures: emit event, alert, keep previous model
   - Timeout: kill job after RETRAIN_TIMEOUT_MINUTES

7. **Storage Management:**
   - Keep last N model versions (configurable, default 10)
   - Clean up old model files to prevent disk bloat
   - Never delete currently active model version

8. **UI/UX Considerations:**
   - Show clear status: idle, running, completed, failed, skipped
   - Display progress during retrain (labels loaded, training, validating)
   - Show metrics comparison (before vs after)
   - Allow viewing retrain logs/errors

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns]
- [Source: _bmad-output/implementation-artifacts/3-6-model-selection-and-activation.md] - Active model management
- [Source: _bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md] - Model interface
- [Source: _bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md] - Scoring integration
- [Source: project-context.md] - Technology stack and rules

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

*Ultimate context engine analysis completed - comprehensive developer guide created*
