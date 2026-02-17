# Epic 3 Prioritized Fix Plan (Story-by-Story with Gates)

Date: 2026-02-12

This plan is based on the Epic 3 breakdown and story artifacts:
- `_bmad-output/implementation-artifacts/3-1-normalize-urls-for-stable-dedupe-keys.md`
- `_bmad-output/implementation-artifacts/3-2-detect-and-link-duplicates.md`
- `_bmad-output/implementation-artifacts/3-3-assign-relevance-scores-baseline.md`
- `_bmad-output/implementation-artifacts/3-4-pluggable-model-interface-and-registry.md`
- `_bmad-output/implementation-artifacts/3-5-parallel-candidate-training-and-evaluation.md`
- `_bmad-output/implementation-artifacts/3-6-model-selection-and-activation.md`
- `_bmad-output/implementation-artifacts/3-7-daily-retrain-for-the-active-model.md`

## Execution mode

- One story at a time.
- Do not start the next story until the current gate passes.
- Keep one branch/PR per story.
- Keep deterministic test behavior (mock provider) for hard gates.
- Hard gate scope is backend/API/ML only.
- Frontend is soft gate (validate after hard gate passes, but do not block story progression on frontend-only issues).

## Pre-Gate (before Story 3.1)

### Objective

Ensure Epic 2 runtime is stable and baseline tooling supports Epic 3 work.

### Tasks

- Verify Epic 2 flow is healthy (run trigger, completion, reports endpoint).
- Ensure ML tests run with a stable import path (`PYTHONPATH=ml`).
- Ensure required ML dependencies are installed for pipeline tests.
- Keep a small deterministic fixture set for duplicate/relevance tests.

### Pre-Gate commands

```bash
docker compose up -d --build
curl -i http://localhost:18080/api/health
curl -i http://localhost:18000/health
curl -i http://localhost:18080/api/reports/runs/latest
PYTHONPATH=ml python3 -m pytest ml/tests/test_ingestion.py
```

### Pass criteria

- API/ML health endpoints return 200.
- Reports endpoint is functional.
- ML ingestion tests execute successfully.

---

## Story 3.1 - Normalize URLs for stable dedupe keys

### Objective

Generate deterministic normalized URL keys and store them for dedupe usage.

### Implementation focus

- Add robust URL normalization logic.
- Strip tracking params and fragments, normalize host/scheme casing.
- Persist normalized key to run items.
- Handle malformed URLs without crashing run.

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

### Pass criteria

- Normalization tests pass.
- `normalized_url` column exists and is populated for ingested results.

---

## Story 3.2 - Detect and link duplicates

### Objective

Link exact and near duplicates to canonical records and hide duplicates by default.

### Implementation focus

- Add duplicate linkage fields (`canonical_id`, `is_duplicate`, `is_hidden`, `duplicate_count`).
- Implement exact-match dedupe on normalized key.
- Implement text-similarity dedupe threshold flow.
- Ensure API retrieval hides duplicates by default and can include them explicitly.

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

### Pass criteria

- Dedupe tests pass.
- Canonical linkage fields are present and populated when duplicates exist.
- API default filtering behavior is validated by tests.

---

## Story 3.3 - Assign relevance scores (baseline)

### Objective

Store baseline relevance scores and expose score fields for retrieval/sorting.

### Implementation focus

- Add `relevance_score`, `scored_at`, `score_version` fields.
- Score canonical/new results with default `0` baseline.
- Ensure range constraints (`-1` to `1`).
- Expose score in API payload and sort options.

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

### Pass criteria

- Scoring tests pass.
- Baseline score fields are persisted and valid.
- API score contract is validated by tests.

---

## Story 3.4 - Pluggable model interface and registry

### Objective

Load model plugins via registry and expose available models safely.

### Implementation focus

- Add model interface contract (`fit`, `predict`).
- Add registry loader from config.
- Discover models at service startup.
- Continue when one model is invalid.
- Keep baseline fallback if registry config missing.

### Gate 3.4

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_model_interface.py ml/tests/test_registry.py

curl -i http://localhost:18000/health
curl -i http://localhost:18000/ml/models
```

### Pass criteria

- Registry and interface tests pass.
- Service reports discovered models.
- Invalid model entries do not block valid models.

---

## Story 3.5 - Parallel candidate training and evaluation

### Objective

Run evaluation jobs for all candidate models with bounded concurrency and stored metrics.

### Implementation focus

- Add evaluation worker pool with configurable `evalWorkers`.
- Queue one evaluation job per model.
- Persist metrics (`precision`, `recall`, `f1`, `accuracy`) per model/version/run.
- Add status/result endpoints for evaluation runs.

### Gate 3.5

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_evaluation_worker.py ml/tests/test_metrics.py ml/tests/test_evaluation_pipeline.py

curl -i -X POST http://localhost:18080/api/ml/evaluations
curl -i http://localhost:18080/api/ml/evaluations/<evaluationId>
curl -i http://localhost:18080/api/ml/evaluations/<evaluationId>/results
```

### Pass criteria

- Evaluation tests pass.
- Concurrency cap behavior is validated by tests.
- Metrics rows persist for each evaluated model.

---

## Story 3.6 - Model selection and activation

### Objective

Compare candidates, activate one model, and support rollback.

### Implementation focus

- Add model comparison and active-model APIs.
- Add activation persistence and history.
- Update scoring pipeline to use active model version.
- Add rollback to previous active versions.

### Gate 3.6

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_model_activation.py ml/tests/test_model_selector.py
./gradlew test --tests "com.jobato.api.controller.MlModelControllerTest" --tests "com.jobato.api.service.MlModelClientTest"

curl -i http://localhost:18080/api/ml/models/comparisons
curl -i -X POST http://localhost:18080/api/ml/models/<modelId>/activate
curl -i http://localhost:18080/api/ml/models/active
```

### Pass criteria

- Activation tests pass.
- Active model endpoint reflects promoted model.
- Rollback behavior is validated by tests.

### Soft gate (frontend)

- Validate model comparison/activation UX behavior and add/update frontend tests.
- Track frontend-only defects separately if backend/API gate already passed.

---

## Story 3.7 - Daily retrain for active model

### Objective

Schedule/trigger retraining, create new model versions, and promote safely.

### Implementation focus

- Add daily scheduler and manual trigger endpoint.
- Retrain active model from new labels.
- Create new version artifact and optional auto-promotion.
- Handle no-new-label path as clean `skipped`.

### Gate 3.7

```bash
PYTHONPATH=ml python3 -m pytest ml/tests/test_retrain_scheduler.py ml/tests/test_retrain_pipeline.py ml/tests/test_retrain_no_labels.py
./gradlew test --tests "com.jobato.api.controller.RetrainControllerTest"

curl -i -X POST http://localhost:18080/api/ml/retrain/trigger
curl -i http://localhost:18080/api/ml/retrain/status
curl -i http://localhost:18080/api/ml/retrain/history
```

### Pass criteria

- Retrain tests pass.
- Manual trigger and status/history APIs work.
- No-label retrain completes without failure and keeps active version unchanged.

### Soft gate (frontend)

- Validate retrain status/history/trigger UX behavior and add/update frontend tests.
- Track frontend-only defects separately if backend/API gate already passed.

---

## Delivery sequence

1. PR A: Story 3.1 + Gate 3.1 evidence
2. PR B: Story 3.2 + Gate 3.2 evidence
3. PR C: Story 3.3 + Gate 3.3 evidence
4. PR D: Story 3.4 + Gate 3.4 evidence
5. PR E: Story 3.5 + Gate 3.5 evidence
6. PR F: Story 3.6 + Gate 3.6 evidence
7. PR G: Story 3.7 + Gate 3.7 evidence
