from __future__ import annotations

from app.services.evaluation_store import EvaluationResultRow, EvaluationStore
from app.services.model_selector import ModelSelector


def test_model_selector_returns_latest_comparisons_with_active_flag(tmp_path):
    store = EvaluationStore(tmp_path / "evaluations.db")
    store.create_run(
        evaluation_id="eval-1",
        dataset_id="dataset-1",
        eval_workers=2,
        total_models=2,
    )
    store.store_result(
        EvaluationResultRow(
            evaluation_id="eval-1",
            model_id="model-a",
            model_version="1.0.0",
            dataset_id="dataset-1",
            status="completed",
            metrics={"precision": 0.8, "recall": 0.7, "f1": 0.75, "accuracy": 0.9},
            error=None,
            duration_ms=100,
            created_at="2026-02-13T10:00:00Z",
        )
    )
    store.store_result(
        EvaluationResultRow(
            evaluation_id="eval-1",
            model_id="model-b",
            model_version="2.0.0",
            dataset_id="dataset-1",
            status="completed",
            metrics={"precision": 0.85, "recall": 0.73, "f1": 0.78, "accuracy": 0.91},
            error=None,
            duration_ms=95,
            created_at="2026-02-13T10:01:00Z",
        )
    )
    store.activate_model(
        model_id="model-b",
        model_version="2.0.0",
        activated_by="tester",
        action="activated",
        evaluation_id="eval-1",
    )

    selector = ModelSelector(store)
    payload = selector.comparisons_payload()

    assert len(payload["comparisons"]) == 2
    model_a = next(item for item in payload["comparisons"] if item["modelId"] == "model-a")
    model_b = next(item for item in payload["comparisons"] if item["modelId"] == "model-b")
    assert model_a["isActive"] is False
    assert model_b["isActive"] is True
