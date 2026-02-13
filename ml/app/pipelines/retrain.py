from __future__ import annotations

import pickle
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from app.registry import ModelRegistry, get_registry
from app.services.evaluation_store import EvaluationStore, RetrainJobRow
from app.services.metrics import calculate_metrics
from app.services.model_versioning import generate_retrain_version


class RetrainInProgressError(RuntimeError):
    pass


@dataclass(frozen=True)
class RetrainSample:
    features: dict[str, Any]
    label: int


class RetrainPipeline:
    def __init__(
        self,
        *,
        store: EvaluationStore,
        registry: ModelRegistry | None = None,
        data_dir: Path | None = None,
        artifact_dir: Path | None = None,
    ) -> None:
        self._store = store
        self._registry = registry or get_registry()
        self._data_dir = data_dir or Path("data")
        self._artifact_dir = artifact_dir or Path("ml/app/models/trained")
        self._run_lock = Lock()

    def run_once(self, *, triggered_by: str) -> RetrainJobRow:
        if not self._run_lock.acquire(blocking=False):
            raise RetrainInProgressError("A retrain job is already running")

        active = self._store.get_active_model()
        if active is None:
            raise ValueError("No active model is available for retraining")

        job_id = str(uuid4())
        self._store.create_retrain_job(
            job_id=job_id,
            model_id=active.model_id,
            previous_version=active.model_version,
            triggered_by=triggered_by,
        )

        try:
            samples = self._load_new_labels(since=self._store.get_last_completed_retrain_at())
            if not samples:
                self._store.complete_retrain_job(
                    job_id=job_id,
                    status="skipped",
                    new_version=active.model_version,
                    label_count=0,
                    metrics={},
                )
                return self._store.get_retrain_job(job_id)

            model = self._registry.get_model(active.model_id)
            if model is None:
                raise ValueError(f"Active model '{active.model_id}' is not registered")

            features = [sample.features for sample in samples]
            labels = [sample.label for sample in samples]

            model.fit(features, labels)
            predictions = model.predict(features)
            binary_predictions = [1 if float(value) >= 0.5 else 0 for value in predictions]
            metrics = calculate_metrics(labels, binary_predictions)

            new_version = generate_retrain_version(active.model_version)
            artifact_path = self._write_artifact(
                model_id=active.model_id,
                model_version=new_version,
                model=model,
                metrics=metrics,
            )
            self._validate_artifact(artifact_path, expected_version=new_version)

            self._store.activate_model(
                model_id=active.model_id,
                model_version=new_version,
                activated_by="retrain",
                action="activated",
            )
            self._store.complete_retrain_job(
                job_id=job_id,
                status="completed",
                new_version=new_version,
                label_count=len(samples),
                metrics=metrics,
            )
            return self._store.get_retrain_job(job_id)
        except Exception as exc:
            self._store.complete_retrain_job(
                job_id=job_id,
                status="failed",
                new_version=active.model_version,
                label_count=0,
                metrics={},
                error_message=str(exc),
            )
            return self._store.get_retrain_job(job_id)
        finally:
            self._run_lock.release()

    def status_payload(self) -> dict[str, Any]:
        latest = self._store.get_latest_retrain_job()
        return {
            "latest": _job_to_payload(latest),
            "running": self._store.has_running_retrain_job(),
        }

    def history_payload(self, *, limit: int = 50) -> dict[str, Any]:
        return {
            "jobs": [_job_to_payload(item) for item in self._store.list_retrain_jobs(limit=limit)],
        }

    def _load_new_labels(self, *, since: str | None) -> list[RetrainSample]:
        db_path = self._resolve_active_db_path()
        if db_path is None or not db_path.exists():
            return []

        where_clause = "WHERE relevance_score IS NOT NULL AND (is_duplicate = 0 OR is_duplicate IS NULL)"
        params: list[str] = []
        if since is not None:
            where_clause += " AND scored_at IS NOT NULL AND scored_at > ?"
            params.append(since)

        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT title, snippet, domain, relevance_score
                FROM run_items
                {where_clause}
                """,
                params,
            ).fetchall()

        samples: list[RetrainSample] = []
        for row in rows:
            score = float(row[3])
            samples.append(
                RetrainSample(
                    features={
                        "title": str(row[0] or ""),
                        "snippet": str(row[1] or ""),
                        "domain": str(row[2] or ""),
                    },
                    label=1 if score > 0 else 0,
                )
            )
        return samples

    def _resolve_active_db_path(self) -> Path | None:
        pointer_path = self._data_dir / "db" / "current-db.txt"
        if not pointer_path.exists():
            return None
        value = pointer_path.read_text(encoding="utf-8").strip()
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else self._data_dir / value

    def _write_artifact(
        self,
        *,
        model_id: str,
        model_version: str,
        model: Any,
        metrics: dict[str, float],
    ) -> Path:
        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self._artifact_dir / f"{model_id}_{model_version}.pkl"
        payload = {
            "modelId": model_id,
            "modelVersion": model_version,
            "trainedAt": _timestamp_now(),
            "metrics": metrics,
            "model": model,
        }
        with artifact_path.open("wb") as handle:
            pickle.dump(payload, handle)
        return artifact_path

    def _validate_artifact(self, artifact_path: Path, *, expected_version: str) -> None:
        with artifact_path.open("rb") as handle:
            payload = pickle.load(handle)
        if payload.get("modelVersion") != expected_version:
            raise ValueError("Saved retrain artifact version mismatch")


def _timestamp_now() -> str:
    value = datetime.now(timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def _job_to_payload(job: RetrainJobRow | None) -> dict[str, Any] | None:
    if job is None:
        return None
    return {
        "jobId": job.job_id,
        "modelId": job.model_id,
        "previousVersion": job.previous_version,
        "newVersion": job.new_version,
        "status": job.status,
        "startedAt": job.started_at,
        "completedAt": job.completed_at,
        "labelCount": job.label_count,
        "metrics": job.metrics,
        "errorMessage": job.error_message,
        "triggeredBy": job.triggered_by,
    }
