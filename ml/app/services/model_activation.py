from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.registry.model_registry import ModelRegistry
from app.services.evaluation_store import ActiveModelRow, EvaluationStore


class ModelActivationError(ValueError):
    pass


@dataclass(frozen=True)
class ActivatedModel:
    model_id: str
    model_version: str
    activated_at: str
    activated_by: str
    evaluation_id: str | None


class ModelActivationService:
    def __init__(self, *, store: EvaluationStore, registry: ModelRegistry) -> None:
        self._store = store
        self._registry = registry

    def activate_model(
        self,
        *,
        model_id: str,
        activated_by: str = "system",
        reason: str | None = None,
    ) -> ActivatedModel:
        if not self._registry.has_model(model_id):
            raise ModelActivationError(f"Model '{model_id}' is not registered")

        latest_result = self._store.get_latest_result_for_model(model_id)
        if latest_result is None:
            raise ModelActivationError(f"Model '{model_id}' has no evaluation results")
        if latest_result.status != "completed":
            raise ModelActivationError(f"Model '{model_id}' latest evaluation is not completed")

        row = self._store.activate_model(
            model_id=model_id,
            model_version=latest_result.model_version,
            activated_by=activated_by,
            action="activated",
            reason=reason,
            evaluation_id=latest_result.evaluation_id,
        )
        return _to_activated_model(row)

    def rollback_model(
        self,
        *,
        model_id: str,
        activated_by: str = "system",
        reason: str | None = None,
    ) -> ActivatedModel:
        if not self._registry.has_model(model_id):
            raise ModelActivationError(f"Model '{model_id}' is not registered")

        history = self._store.get_activation_history(limit=200)
        target = next((item for item in history if item.model_id == model_id), None)
        if target is None:
            raise ModelActivationError(f"Model '{model_id}' has no activation history")

        row = self._store.activate_model(
            model_id=target.model_id,
            model_version=target.model_version,
            activated_by=activated_by,
            action="rollback",
            reason=reason,
            evaluation_id=target.evaluation_id,
        )
        return _to_activated_model(row)

    def get_active_model(self) -> ActivatedModel | None:
        row = self._store.get_active_model()
        if row is None:
            return None
        return _to_activated_model(row)

    def active_model_payload(self) -> dict[str, Any]:
        active = self.get_active_model()
        if active is None:
            return {"activeModel": None}
        return {
            "activeModel": {
                "modelId": active.model_id,
                "modelVersion": active.model_version,
                "activatedAt": active.activated_at,
                "activatedBy": active.activated_by,
                "evaluationId": active.evaluation_id,
            }
        }

    def history_payload(self) -> dict[str, Any]:
        return {
            "history": [
                {
                    "modelId": item.model_id,
                    "modelVersion": item.model_version,
                    "action": item.action,
                    "timestamp": item.timestamp,
                    "previousModelId": item.previous_model_id,
                    "previousModelVersion": item.previous_model_version,
                    "reason": item.reason,
                    "evaluationId": item.evaluation_id,
                }
                for item in self._store.get_activation_history()
            ]
        }


def _to_activated_model(row: ActiveModelRow) -> ActivatedModel:
    return ActivatedModel(
        model_id=row.model_id,
        model_version=row.model_version,
        activated_at=row.activated_at,
        activated_by=row.activated_by,
        evaluation_id=row.evaluation_id,
    )
