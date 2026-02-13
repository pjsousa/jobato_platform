from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from app.registry import ModelRegistry, get_registry
from app.services.evaluation_store import EvaluationResultRow, EvaluationStore
from app.services.evaluation_worker import run_worker_pool
from app.services.metrics import calculate_metrics


logger = logging.getLogger(__name__)
DEFAULT_EVAL_WORKERS = 3
MAX_EVAL_WORKERS = 10


@dataclass(frozen=True)
class EvaluationDataset:
    dataset_id: str
    features: list[dict[str, Any]]
    labels: list[int]


@dataclass(frozen=True)
class EvaluationJob:
    model_id: str
    model_version: str
    model: Any


class EvaluationDatasetProvider:
    def __init__(self, *, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or Path(os.getenv("DATA_DIR", "data"))

    def load_dataset(self) -> EvaluationDataset:
        db_path = self._resolve_active_db_path()
        if db_path is None or not db_path.exists():
            return _default_dataset()

        rows = _load_rows_from_run_items(db_path)
        if not rows:
            return _default_dataset()

        features: list[dict[str, Any]] = []
        labels: list[int] = []
        for title, snippet, domain, relevance_score in rows:
            features.append({"title": title, "snippet": snippet, "domain": domain})
            labels.append(1 if float(relevance_score) > 0 else 0)

        dataset_id = f"{db_path.name}:{len(rows)}"
        return EvaluationDataset(dataset_id=dataset_id, features=features, labels=labels)

    def _resolve_active_db_path(self) -> Path | None:
        pointer_path = self._data_dir / "db" / "current-db.txt"
        if not pointer_path.exists():
            return None
        value = pointer_path.read_text(encoding="utf-8").strip()
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else self._data_dir / value


class EvaluationPipeline:
    def __init__(
        self,
        *,
        store: EvaluationStore,
        registry: ModelRegistry | None = None,
        dataset_provider: EvaluationDatasetProvider | None = None,
        eval_workers: int | None = None,
    ) -> None:
        self._store = store
        self._registry = registry or get_registry()
        self._dataset_provider = dataset_provider or EvaluationDatasetProvider()
        self._eval_workers = _resolve_eval_workers(eval_workers)

    @property
    def eval_workers(self) -> int:
        return self._eval_workers

    def trigger_evaluation(self) -> dict[str, Any]:
        dataset = self._dataset_provider.load_dataset()
        jobs = self._build_jobs()
        evaluation_id = str(uuid4())
        self._store.create_run(
            evaluation_id=evaluation_id,
            dataset_id=dataset.dataset_id,
            eval_workers=self._eval_workers,
            total_models=len(jobs),
        )
        asyncio.create_task(self._run_evaluation(evaluation_id=evaluation_id, dataset=dataset, jobs=jobs))
        return {
            "evaluationId": evaluation_id,
            "status": "running",
            "datasetId": dataset.dataset_id,
            "totalModels": len(jobs),
            "evalWorkers": self._eval_workers,
        }

    async def _run_evaluation(
        self,
        *,
        evaluation_id: str,
        dataset: EvaluationDataset,
        jobs: list[EvaluationJob],
    ) -> None:
        async def evaluate_job(job: EvaluationJob) -> None:
            started = time.perf_counter()
            try:
                await asyncio.to_thread(job.model.fit, dataset.features, dataset.labels)
                predictions = await asyncio.to_thread(job.model.predict, dataset.features)
                binary_predictions = [_to_binary_prediction(value) for value in predictions]
                metrics = calculate_metrics(dataset.labels, binary_predictions)
                status = "completed"
                error = None
                failed_increment = 0
            except Exception as exc:
                logger.warning("evaluation.model_failed evaluation_id=%s model=%s error=%s", evaluation_id, job.model_id, exc)
                metrics = {}
                status = "failed"
                error = str(exc)
                failed_increment = 1

            duration_ms = int((time.perf_counter() - started) * 1000)
            self._store.store_result(
                EvaluationResultRow(
                    evaluation_id=evaluation_id,
                    model_id=job.model_id,
                    model_version=job.model_version,
                    dataset_id=dataset.dataset_id,
                    status=status,
                    metrics=metrics,
                    error=error,
                    duration_ms=duration_ms,
                    created_at=_timestamp_now(),
                )
            )
            self._store.update_progress(evaluation_id=evaluation_id, failed_increment=failed_increment)

        await run_worker_pool(jobs, worker_count=self._eval_workers, worker_fn=evaluate_job)
        self._store.complete_run(evaluation_id=evaluation_id)

    def _build_jobs(self) -> list[EvaluationJob]:
        jobs: list[EvaluationJob] = []
        for model_entry in self._registry.get_available_models():
            model_id = str(model_entry["identifier"])
            model_version = str(model_entry.get("version") or "unknown")
            model = self._registry.get_model(model_id)
            if model is None:
                continue
            jobs.append(EvaluationJob(model_id=model_id, model_version=model_version, model=model))
        return jobs


def get_status(store: EvaluationStore, evaluation_id: str) -> dict[str, Any] | None:
    row = store.get_run(evaluation_id)
    if row is None:
        return None
    return {
        "evaluationId": row.evaluation_id,
        "status": row.status,
        "datasetId": row.dataset_id,
        "evalWorkers": row.eval_workers,
        "totalModels": row.total_models,
        "completedModels": row.completed_models,
        "failedModels": row.failed_models,
        "startedAt": row.started_at,
        "completedAt": row.completed_at,
    }


def get_results(store: EvaluationStore, evaluation_id: str) -> dict[str, Any]:
    rows = store.get_results(evaluation_id)
    return {
        "evaluationId": evaluation_id,
        "results": [
            {
                "modelId": row.model_id,
                "modelVersion": row.model_version,
                "datasetId": row.dataset_id,
                "status": row.status,
                "metrics": row.metrics,
                "error": row.error,
                "durationMs": row.duration_ms,
                "createdAt": row.created_at,
            }
            for row in rows
        ],
    }


def _resolve_eval_workers(explicit: int | None) -> int:
    if explicit is not None:
        return _sanitize_workers(explicit)
    loaded = _load_eval_workers_from_config()
    return _sanitize_workers(loaded)


def _load_eval_workers_from_config() -> int:
    config_dir = Path(os.getenv("CONFIG_DIR", "config"))
    config_path = config_dir / "ml" / "ml-config.yaml"
    if not config_path.exists():
        return DEFAULT_EVAL_WORKERS
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_EVAL_WORKERS
    if not isinstance(payload, dict):
        return DEFAULT_EVAL_WORKERS
    value = payload.get("evalWorkers", DEFAULT_EVAL_WORKERS)
    if isinstance(value, int):
        return value
    return DEFAULT_EVAL_WORKERS


def _sanitize_workers(value: int) -> int:
    return max(1, min(MAX_EVAL_WORKERS, int(value)))


def _to_binary_prediction(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if float(value) >= 0.5 else 0
    return 0


def _load_rows_from_run_items(db_path: Path) -> list[tuple[str, str, str, float]]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT title, snippet, domain, relevance_score
            FROM run_items
            WHERE relevance_score IS NOT NULL AND (is_duplicate = 0 OR is_duplicate IS NULL)
            """
        ).fetchall()
    return [(str(row[0] or ""), str(row[1] or ""), str(row[2] or ""), float(row[3])) for row in rows]


def _default_dataset() -> EvaluationDataset:
    return EvaluationDataset(
        dataset_id="synthetic-default",
        features=[
            {"title": "Relevant role", "snippet": "Python backend engineer", "domain": "example.com"},
            {"title": "Irrelevant role", "snippet": "Retail cashier", "domain": "example.com"},
        ],
        labels=[1, 0],
    )


def _timestamp_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
