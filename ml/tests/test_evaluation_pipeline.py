import asyncio
from dataclasses import dataclass
from pathlib import Path

from app.pipelines.evaluation import EvaluationDataset, EvaluationPipeline, get_results, get_status
from app.services.evaluation_store import EvaluationStore


class _SuccessModel:
    def fit(self, X, y):
        return self

    def predict(self, X):
        return [1, 0, 1, 0]


class _FailingModel:
    def fit(self, X, y):
        raise RuntimeError("training failed")

    def predict(self, X):
        return [0 for _ in X]


@dataclass
class _FakeRegistry:
    models: dict[str, object]
    versions: dict[str, str]

    def get_available_models(self):
        return [
            {"identifier": model_id, "version": self.versions[model_id]}
            for model_id in self.models
        ]

    def get_model(self, identifier: str):
        return self.models.get(identifier)


class _StaticDatasetProvider:
    def load_dataset(self) -> EvaluationDataset:
        return EvaluationDataset(
            dataset_id="dataset-1",
            features=[
                {"title": "a", "snippet": "a", "domain": "x"},
                {"title": "b", "snippet": "b", "domain": "x"},
                {"title": "c", "snippet": "c", "domain": "x"},
                {"title": "d", "snippet": "d", "domain": "x"},
            ],
            labels=[1, 0, 1, 0],
        )


def test_evaluation_pipeline_persists_metrics_and_failures(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path / "evaluations.db")
    registry = _FakeRegistry(
        models={"ok-model": _SuccessModel(), "bad-model": _FailingModel()},
        versions={"ok-model": "1.2.3", "bad-model": "2.0.0"},
    )
    pipeline = EvaluationPipeline(
        store=store,
        registry=registry,
        dataset_provider=_StaticDatasetProvider(),
        eval_workers=2,
    )

    async def run_case() -> str:
        payload = pipeline.trigger_evaluation()
        evaluation_id = payload["evaluationId"]
        for _ in range(50):
            status_payload = get_status(store, evaluation_id)
            if status_payload is not None and status_payload["status"] != "running":
                return evaluation_id
            await asyncio.sleep(0.02)
        return evaluation_id

    evaluation_id = asyncio.run(run_case())

    status_payload = get_status(store, evaluation_id)
    assert status_payload is not None
    assert status_payload["status"] == "partial_failed"
    assert status_payload["failedModels"] == 1
    assert status_payload["completedModels"] == 2

    results_payload = get_results(store, evaluation_id)
    assert len(results_payload["results"]) == 2

    ok_result = next(item for item in results_payload["results"] if item["modelId"] == "ok-model")
    assert ok_result["modelVersion"] == "1.2.3"
    assert ok_result["datasetId"] == "dataset-1"
    assert set(ok_result["metrics"].keys()) == {"precision", "recall", "f1", "accuracy"}

    failed_result = next(item for item in results_payload["results"] if item["modelId"] == "bad-model")
    assert failed_result["status"] == "failed"
    assert failed_result["metrics"] == {}
    assert failed_result["error"] is not None
