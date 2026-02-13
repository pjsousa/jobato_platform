from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.evaluation_store import EvaluationStore


@dataclass(frozen=True)
class ModelComparison:
    model_id: str
    model_version: str
    evaluation_id: str
    dataset_id: str
    status: str
    metrics: dict[str, float]
    error: str | None
    created_at: str
    is_active: bool


class ModelSelector:
    def __init__(self, store: EvaluationStore) -> None:
        self._store = store

    def get_comparisons(self) -> list[ModelComparison]:
        active = self._store.get_active_model()
        results = self._store.get_latest_results_per_model()
        comparisons: list[ModelComparison] = []
        for row in results:
            comparisons.append(
                ModelComparison(
                    model_id=row.model_id,
                    model_version=row.model_version,
                    evaluation_id=row.evaluation_id,
                    dataset_id=row.dataset_id,
                    status=row.status,
                    metrics=row.metrics,
                    error=row.error,
                    created_at=row.created_at,
                    is_active=(
                        active is not None
                        and active.model_id == row.model_id
                        and active.model_version == row.model_version
                    ),
                )
            )
        return comparisons

    def comparisons_payload(self) -> dict[str, Any]:
        return {
            "comparisons": [
                {
                    "modelId": item.model_id,
                    "modelVersion": item.model_version,
                    "evaluationId": item.evaluation_id,
                    "datasetId": item.dataset_id,
                    "status": item.status,
                    "metrics": item.metrics,
                    "error": item.error,
                    "evaluatedAt": item.created_at,
                    "isActive": item.is_active,
                }
                for item in self.get_comparisons()
            ]
        }
