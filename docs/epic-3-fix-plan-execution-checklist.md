# Epic 3 Fix Plan - Execution Checklist

Date: 2026-02-12
Mode: Story-by-story, gated

## How to use

- Complete one story at a time.
- Reproduce each gate yourself before approving merge.
- Keep one branch/PR per story.
- Keep hard gates deterministic (mock provider/data fixtures).
- Hard gate scope is backend/API/ML only.
- Frontend validation is soft gate (run after hard gate; do not block story progression on frontend-only issues).

## Hard vs soft gate policy

- [ ] Hard gate (required): backend/API/ML acceptance criteria and gate commands pass.
- [ ] Soft gate (advisory): frontend behavior/tests validated and logged.
- [ ] Frontend-only issues, if any, are tracked as follow-up tasks without blocking next story.

---

## Global pre-gate

- [ ] Docker services are up and healthy.
- [ ] Epic 2 flow still works before Epic 3 changes.
- [ ] ML tests run with stable import path (`PYTHONPATH=ml`).

Commands:

```bash
docker compose up -d --build
curl -i http://localhost:18080/api/health
curl -i http://localhost:18000/health
curl -i http://localhost:18080/api/reports/runs/latest
PYTHONPATH=ml python3 -m pytest ml/tests/test_ingestion.py
```

---

## Story 3.1 - Normalize URLs for stable dedupe keys

### Implementation checklist

- [ ] URL normalization logic added and deterministic.
- [ ] Tracking params/fragments removed; casing normalized.
- [ ] `normalized_url` persisted to run items.
- [ ] Malformed URL handling does not break run.
- [ ] Tests added/updated.

### Gate 3.1

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_url_normalization.py ml/tests/test_ingestion.py

RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

sqlite3 "data/db/runs/${RUN_ID}.db" "PRAGMA table_info(run_items);"
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE normalized_url IS NOT NULL;"
```

### Gate pass checks

- [ ] Tests pass.
- [ ] `normalized_url` column exists.
- [ ] At least one ingested row has `normalized_url`.

---

## Story 3.2 - Detect and link duplicates

### Implementation checklist

- [ ] Canonical linkage fields added (`canonical_id`, `is_duplicate`, `is_hidden`, `duplicate_count`).
- [ ] Exact dedupe by normalized URL works.
- [ ] Similarity dedupe works with defined threshold.
- [ ] API hides duplicates by default and supports opt-in include.
- [ ] Tests added/updated.

### Gate 3.2

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_dedupe.py ml/tests/test_ingestion_dedupe.py
./gradlew test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"

RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE is_duplicate = 1;"
sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT COUNT(*) FROM run_items WHERE canonical_id IS NOT NULL;"
```

### Gate pass checks

- [ ] Dedupe tests pass.
- [ ] API tests for hidden-by-default behavior pass.
- [ ] Duplicate linkage fields are populated when duplicates are present.

---

## Story 3.3 - Assign relevance scores (baseline)

### Implementation checklist

- [ ] Score fields added (`relevance_score`, `scored_at`, `score_version`).
- [ ] Baseline score assignment implemented (`0`).
- [ ] Score range constraints enforced.
- [ ] API returns score fields and sorting behavior.
- [ ] Tests added/updated.

### Gate 3.3

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_scoring.py ml/tests/test_ingestion_scoring.py
./gradlew test --tests "com.jobato.api.controller.ResultsControllerTest" --tests "com.jobato.api.service.ResultServiceTest"

RUN_ID=$(curl -s -X POST http://localhost:18080/api/runs | python3 -c 'import sys,json; print(json.load(sys.stdin)["runId"])')
for i in {1..30}; do
  STATUS=$(curl -s "http://localhost:18080/api/runs/$RUN_ID" | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])')
  [ "$STATUS" != "running" ] && break
  sleep 2
done

sqlite3 "data/db/runs/${RUN_ID}.db" "SELECT MIN(relevance_score), MAX(relevance_score), COUNT(*) FROM run_items WHERE relevance_score IS NOT NULL;"
```

### Gate pass checks

- [ ] Scoring tests pass.
- [ ] API score contract tests pass.
- [ ] Scores exist and are within allowed range.

---

## Story 3.4 - Pluggable model interface and registry

### Implementation checklist

- [ ] Model interface contract created.
- [ ] Registry loader/discovery implemented.
- [ ] Startup model discovery integrated.
- [ ] Invalid model handling keeps valid models available.
- [ ] Baseline fallback retained.
- [ ] Tests added/updated.

### Gate 3.4

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_model_interface.py ml/tests/test_registry.py
curl -i http://localhost:18000/health
curl -i http://localhost:18000/ml/models
```

### Gate pass checks

- [ ] Registry tests pass.
- [ ] Model listing endpoint works.
- [ ] Invalid plugin does not break startup discovery.

---

## Story 3.5 - Parallel candidate training and evaluation

### Implementation checklist

- [ ] Evaluation worker pool implemented with `evalWorkers` cap.
- [ ] One evaluation job per model is enqueued.
- [ ] Metrics calculation implemented (precision/recall/f1/accuracy).
- [ ] Evaluation result persistence implemented.
- [ ] Evaluation status/results APIs implemented.
- [ ] Tests added/updated.

### Gate 3.5

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_evaluation_worker.py ml/tests/test_metrics.py ml/tests/test_evaluation_pipeline.py
curl -i -X POST http://localhost:18080/api/ml/evaluations
curl -i http://localhost:18080/api/ml/evaluations/<evaluationId>
curl -i http://localhost:18080/api/ml/evaluations/<evaluationId>/results
```

### Gate pass checks

- [ ] Evaluation tests pass.
- [ ] Concurrency limit behavior is verified by tests.
- [ ] Evaluation APIs return expected status and metrics.

---

## Story 3.6 - Model selection and activation

### Implementation checklist

- [ ] Model comparison endpoint(s) implemented.
- [ ] Active model activation endpoint implemented.
- [ ] Activation history persisted.
- [ ] Rollback path implemented.
- [ ] Scoring pipeline reads active model.
- [ ] Tests added/updated.

### Gate 3.6

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_model_activation.py ml/tests/test_model_selector.py
./gradlew test --tests "com.jobato.api.controller.MlModelControllerTest" --tests "com.jobato.api.service.MlModelClientTest"
curl -i http://localhost:18080/api/ml/models/comparisons
curl -i -X POST http://localhost:18080/api/ml/models/<modelId>/activate
curl -i http://localhost:18080/api/ml/models/active
```

### Gate pass checks

- [ ] Activation tests pass.
- [ ] Active model endpoint reflects promoted model.
- [ ] Rollback behavior is validated by tests.

### Soft gate (frontend)

- [ ] Model comparison/activation frontend behavior validated manually.
- [ ] Frontend tests updated or added for models UI path.
- [ ] Any frontend-only gaps are documented as follow-up issues.

---

## Story 3.7 - Daily retrain for the active model

### Implementation checklist

- [ ] Daily retrain scheduler implemented.
- [ ] Manual retrain trigger endpoint implemented.
- [ ] Retrain history/status persistence implemented.
- [ ] New version generation + activation integration works.
- [ ] No-new-label flow returns clean skipped status.
- [ ] Tests added/updated.

### Gate 3.7

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_retrain_scheduler.py ml/tests/test_retrain_pipeline.py ml/tests/test_retrain_no_labels.py
./gradlew test --tests "com.jobato.api.controller.RetrainControllerTest"
curl -i -X POST http://localhost:18080/api/ml/retrain/trigger
curl -i http://localhost:18080/api/ml/retrain/status
curl -i http://localhost:18080/api/ml/retrain/history
```

### Gate pass checks

- [ ] Retrain tests pass.
- [ ] Manual trigger/status/history APIs work.
- [ ] No-new-label scenario passes without failure and keeps active version.

### Soft gate (frontend)

- [ ] Retrain frontend status/history/trigger behavior validated manually.
- [ ] Frontend tests updated or added for retrain UI path.
- [ ] Any frontend-only gaps are documented as follow-up issues.

---

## Evidence template (copy per story)

```md
### Story X.Y Evidence
- Branch/PR:
- Commit SHA:
- Gate commands run:
- Gate outputs saved at:
- Pass/Fail:
- Notes:
```
