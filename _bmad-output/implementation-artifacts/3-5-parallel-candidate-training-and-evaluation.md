---
epic: 3
story: 5
title: Parallel candidate training and evaluation
status: ready-for-dev
---

# Story 3.5: Parallel candidate training and evaluation

Status: ready-for-dev

## Story

As a user,
I want multiple candidate models trained and evaluated in parallel on the same dataset,
So that I can compare their metrics side-by-side.

## Acceptance Criteria

**AC 1: Parallel evaluation job enqueueing**

**Given** N registered models
**When** an evaluation run is requested
**Then** an evaluation job is enqueued for each model
**And** a worker pool of size evalWorkers processes jobs concurrently

**AC 2: Concurrency control via evalWorkers**

**Given** evalWorkers is configured to 3
**When** an evaluation run is requested
**Then** at most 3 model evaluations run at the same time
**And** remaining jobs are queued until a worker is available

**AC 3: Metrics storage with versioning**

**Given** evaluation completes
**When** results are stored
**Then** each model has a metrics record tied to the run ID and model version
**And** the metrics record includes dataset identifiers

**AC 4: Default metrics calculation**

**Given** default metrics are required
**When** evaluation runs
**Then** it produces precision, recall, F1, and accuracy
**And** the schema is extensible for additional metrics

## Tasks / Subtasks

- [ ] Task 1: Create evaluation job queue/worker system (AC: #1, #2)
  - [ ] Design job queue data structure (SQLite table or in-memory with persistence)
  - [ ] Implement worker pool with configurable size (evalWorkers)
  - [ ] Create job enqueueing logic for N models
  - [ ] Implement concurrent job processing with rate limiting
  
- [ ] Task 2: Implement model training executor (AC: #1)
  - [ ] Create training pipeline wrapper that works with registered models
  - [ ] Load dataset for evaluation from labeled results
  - [ ] Execute model.fit() with standardized interface
  - [ ] Handle training errors gracefully
  
- [ ] Task 3: Implement evaluation metrics calculator (AC: #4)
  - [ ] Create metrics calculation for precision, recall, F1, accuracy
  - [ ] Design extensible metrics schema
  - [ ] Generate predictions using model.predict()
  - [ ] Compare predictions against ground truth labels
  
- [ ] Task 4: Persist evaluation results (AC: #3)
  - [ ] Create evaluation_results table/schema
  - [ ] Store metrics with run ID, model version, timestamp
  - [ ] Link to dataset identifier
  - [ ] Ensure idempotent writes for re-runs
  
- [ ] Task 5: Create API endpoints for evaluation management (AC: #1, #3)
  - [ ] POST /api/ml/evaluations - Trigger evaluation run
  - [ ] GET /api/ml/evaluations/{id} - Get evaluation status
  - [ ] GET /api/ml/evaluations/{id}/results - Get detailed results
  
- [ ] Task 6: Add Redis event publishing (AC: #1, #3)
  - [ ] Publish evaluation.started event
  - [ ] Publish evaluation.completed event with metrics
  - [ ] Publish evaluation.failed event on errors
  
- [ ] Task 7: Testing (AC: #1, #2, #3, #4)
  - [ ] Unit tests for worker pool concurrency
  - [ ] Unit tests for metrics calculation
  - [ ] Integration tests for full evaluation flow
  - [ ] Test with mock models to verify parallel execution

## Dev Notes

### Context from Previous Stories (3.1-3.4)

From Story 3.4 (Pluggable model interface), we established:
- Models must implement `fit(X, y)` and `predict(X)` interface
- Model registry discovers models dynamically
- Model identifiers are stored for selection

From Story 3.3 (Baseline scoring), we established:
- Scores range from -1 to 1
- Default score is 0 when no model exists
- Model versioning is required for tracking

From Stories 3.1-3.2 (Deduplication), we have:
- Normalized URL keys for deduplication
- Canonical record linking
- Duplicate detection pipeline

### Architecture Compliance

**ML Service Structure:**
- Location: `ml/app/pipelines/evaluation.py` (new file)
- Worker pool: `ml/app/services/evaluation_worker.py` (new file)
- Metrics calculator: `ml/app/services/metrics.py` (new file)
- DB models: `ml/app/db/models.py` (extend with EvaluationResult)

**Data Architecture:**
- SQLite storage for evaluation results (follow pointer file pattern)
- Evaluation jobs table separate from active DB
- Raw metrics stored as JSON for extensibility

**Event Patterns:**
- Stream: `ml:run-events`
- Event types: `evaluation.started`, `evaluation.completed`, `evaluation.failed`
- Envelope: `{eventId, eventType, eventVersion: 1, occurredAt, runId, payload}`

**API Patterns:**
- ML service exposes internal endpoints (not public API)
- Use FastAPI router in `ml/app/routes/evaluation.py`
- RFC 7807 error responses

### Technical Requirements

**Python Dependencies:**
- scikit-learn (for model interface compatibility)
- numpy/pandas (for dataset handling)
- SQLAlchemy (for persistence)
- pytest (for testing)

**Configuration:**
- evalWorkers: int (default: 3, max: 10)
- evaluationTimeout: int (seconds, default: 3600)
- Supported metrics: precision, recall, f1, accuracy (extensible)

**Worker Pool Design:**
```python
# Conceptual design
class EvaluationWorkerPool:
    def __init__(self, num_workers: int):
        self.queue = Queue()
        self.workers = [Worker() for _ in range(num_workers)]
    
    async def enqueue(self, job: EvaluationJob):
        # Add to queue
        
    async def process(self):
        # Workers pick jobs concurrently
```

**Metrics Schema:**
```json
{
  "evaluationId": "uuid",
  "runId": "uuid",
  "modelId": "string",
  "modelVersion": "string",
  "datasetId": "string",
  "metrics": {
    "precision": 0.85,
    "recall": 0.72,
    "f1": 0.78,
    "accuracy": 0.91
  },
  "timestamp": "2026-02-09T10:00:00Z",
  "duration": 245
}
```

### Project Structure Notes

**New Files to Create:**
```
ml/
├── app/
│   ├── pipelines/
│   │   └── evaluation.py          # Main evaluation orchestrator
│   ├── services/
│   │   ├── evaluation_worker.py   # Worker pool implementation
│   │   └── metrics.py             # Metrics calculation
│   ├── routes/
│   │   └── evaluation.py          # FastAPI endpoints
│   └── db/
│       └── models.py              # Add EvaluationResult model
```

**Database Migrations:**
- Add `evaluation_results` table
- Add `evaluation_jobs` table (for queue persistence)
- Link to existing `feedback_labels` for ground truth

### Integration Points

**Input:**
- Model registry (from Story 3.4)
- Labeled results from feedback system
- Configuration from `config/ml/ml-config.yaml`

**Output:**
- Evaluation results stored in SQLite
- Redis events for API consumption
- Metrics available for model selection (Story 3.6)

### Critical Implementation Notes

1. **Idempotency:** Evaluation jobs must be idempotent - same model + dataset should produce same results

2. **Resource Management:** Worker pool must respect evalWorkers limit to prevent resource exhaustion

3. **Error Handling:** 
   - Failed model training should not block other evaluations
   - Partial failures should be recorded with error details
   - Use try/except with specific error logging

4. **Dataset Consistency:**
   - All models evaluated on same dataset snapshot
   - Cache dataset to prevent regeneration during evaluation

5. **Extensibility:**
   - Metrics schema must support custom metrics
   - Worker pool should support different job types in future

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Event System Patterns]
- [Source: _bmad-output/planning-artifacts/project-context.md#Python Rules]
- [Source: _bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md] - Model interface established

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

*Ultimate context engine analysis completed - comprehensive developer guide created*
