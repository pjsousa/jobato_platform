from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


@dataclass(frozen=True)
class EvaluationRunRow:
    evaluation_id: str
    status: str
    dataset_id: str
    eval_workers: int
    total_models: int
    completed_models: int
    failed_models: int
    started_at: str
    completed_at: str | None


@dataclass(frozen=True)
class EvaluationResultRow:
    evaluation_id: str
    model_id: str
    model_version: str
    dataset_id: str
    status: str
    metrics: dict[str, float]
    error: str | None
    duration_ms: int
    created_at: str


@dataclass(frozen=True)
class ActiveModelRow:
    model_id: str
    model_version: str
    activated_at: str
    activated_by: str
    evaluation_id: str | None


@dataclass(frozen=True)
class ModelActivationHistoryRow:
    model_id: str
    model_version: str
    action: str
    timestamp: str
    previous_model_id: str | None
    previous_model_version: str | None
    reason: str | None
    evaluation_id: str | None


class EvaluationStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ensure_schema()

    def create_run(
        self,
        *,
        evaluation_id: str,
        dataset_id: str,
        eval_workers: int,
        total_models: int,
    ) -> None:
        started_at = _timestamp_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_runs (
                    evaluation_id,
                    status,
                    dataset_id,
                    eval_workers,
                    total_models,
                    completed_models,
                    failed_models,
                    started_at,
                    completed_at
                ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, NULL)
                """,
                (evaluation_id, "running", dataset_id, eval_workers, total_models, started_at),
            )
            conn.commit()

    def update_progress(self, *, evaluation_id: str, failed_increment: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE evaluation_runs
                SET completed_models = completed_models + 1,
                    failed_models = failed_models + ?
                WHERE evaluation_id = ?
                """,
                (failed_increment, evaluation_id),
            )
            conn.commit()

    def complete_run(self, *, evaluation_id: str) -> None:
        row = self.get_run(evaluation_id)
        if row is None:
            return
        status = "completed" if row.failed_models == 0 else "partial_failed"
        completed_at = _timestamp_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE evaluation_runs
                SET status = ?, completed_at = ?
                WHERE evaluation_id = ?
                """,
                (status, completed_at, evaluation_id),
            )
            conn.commit()

    def store_result(self, row: EvaluationResultRow) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_results (
                    evaluation_id,
                    model_id,
                    model_version,
                    dataset_id,
                    status,
                    metrics_json,
                    error,
                    duration_ms,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evaluation_id, model_id, model_version) DO UPDATE SET
                    status = excluded.status,
                    metrics_json = excluded.metrics_json,
                    error = excluded.error,
                    duration_ms = excluded.duration_ms,
                    created_at = excluded.created_at
                """,
                (
                    row.evaluation_id,
                    row.model_id,
                    row.model_version,
                    row.dataset_id,
                    row.status,
                    json.dumps(row.metrics),
                    row.error,
                    row.duration_ms,
                    row.created_at,
                ),
            )
            conn.commit()

    def get_run(self, evaluation_id: str) -> EvaluationRunRow | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT evaluation_id, status, dataset_id, eval_workers,
                       total_models, completed_models, failed_models,
                       started_at, completed_at
                FROM evaluation_runs
                WHERE evaluation_id = ?
                """,
                (evaluation_id,),
            ).fetchone()
        if row is None:
            return None
        return EvaluationRunRow(
            evaluation_id=row[0],
            status=row[1],
            dataset_id=row[2],
            eval_workers=row[3],
            total_models=row[4],
            completed_models=row[5],
            failed_models=row[6],
            started_at=row[7],
            completed_at=row[8],
        )

    def get_results(self, evaluation_id: str) -> list[EvaluationResultRow]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT evaluation_id, model_id, model_version, dataset_id,
                       status, metrics_json, error, duration_ms, created_at
                FROM evaluation_results
                WHERE evaluation_id = ?
                ORDER BY model_id ASC
                """,
                (evaluation_id,),
            ).fetchall()
        return [
            EvaluationResultRow(
                evaluation_id=row[0],
                model_id=row[1],
                model_version=row[2],
                dataset_id=row[3],
                status=row[4],
                metrics=json.loads(row[5]) if row[5] else {},
                error=row[6],
                duration_ms=row[7],
                created_at=row[8],
            )
            for row in rows
        ]

    def get_latest_results_per_model(self) -> list[EvaluationResultRow]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT er.evaluation_id,
                       er.model_id,
                       er.model_version,
                       er.dataset_id,
                       er.status,
                       er.metrics_json,
                       er.error,
                       er.duration_ms,
                       er.created_at
                FROM evaluation_results er
                INNER JOIN (
                    SELECT model_id, model_version, MAX(created_at) AS max_created_at
                    FROM evaluation_results
                    GROUP BY model_id, model_version
                ) latest
                    ON latest.model_id = er.model_id
                   AND latest.model_version = er.model_version
                   AND latest.max_created_at = er.created_at
                ORDER BY er.model_id ASC, er.model_version ASC
                """
            ).fetchall()
        return [
            EvaluationResultRow(
                evaluation_id=row[0],
                model_id=row[1],
                model_version=row[2],
                dataset_id=row[3],
                status=row[4],
                metrics=json.loads(row[5]) if row[5] else {},
                error=row[6],
                duration_ms=row[7],
                created_at=row[8],
            )
            for row in rows
        ]

    def get_latest_result_for_model(self, model_id: str) -> EvaluationResultRow | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT evaluation_id, model_id, model_version, dataset_id,
                       status, metrics_json, error, duration_ms, created_at
                FROM evaluation_results
                WHERE model_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (model_id,),
            ).fetchone()
        if row is None:
            return None
        return EvaluationResultRow(
            evaluation_id=row[0],
            model_id=row[1],
            model_version=row[2],
            dataset_id=row[3],
            status=row[4],
            metrics=json.loads(row[5]) if row[5] else {},
            error=row[6],
            duration_ms=row[7],
            created_at=row[8],
        )

    def get_active_model(self) -> ActiveModelRow | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT model_id, model_version, activated_at, activated_by, evaluation_id
                FROM active_models
                WHERE is_active = 1
                ORDER BY activated_at DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return ActiveModelRow(
            model_id=row[0],
            model_version=row[1],
            activated_at=row[2],
            activated_by=row[3],
            evaluation_id=row[4],
        )

    def activate_model(
        self,
        *,
        model_id: str,
        model_version: str,
        activated_by: str,
        action: str,
        reason: str | None = None,
        evaluation_id: str | None = None,
    ) -> ActiveModelRow:
        timestamp = _timestamp_now()
        with self._lock:
            with self._connect() as conn:
                previous = conn.execute(
                    """
                    SELECT model_id, model_version
                    FROM active_models
                    WHERE is_active = 1
                    ORDER BY activated_at DESC
                    LIMIT 1
                    """
                ).fetchone()

                conn.execute("UPDATE active_models SET is_active = 0 WHERE is_active = 1")
                conn.execute(
                    """
                    INSERT INTO active_models (
                        model_id,
                        model_version,
                        activated_at,
                        activated_by,
                        evaluation_id,
                        is_active
                    ) VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (model_id, model_version, timestamp, activated_by, evaluation_id),
                )
                conn.execute(
                    """
                    INSERT INTO model_activation_history (
                        model_id,
                        model_version,
                        action,
                        timestamp,
                        previous_model_id,
                        previous_model_version,
                        reason,
                        evaluation_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        model_id,
                        model_version,
                        action,
                        timestamp,
                        previous[0] if previous else None,
                        previous[1] if previous else None,
                        reason,
                        evaluation_id,
                    ),
                )
                conn.commit()

        return ActiveModelRow(
            model_id=model_id,
            model_version=model_version,
            activated_at=timestamp,
            activated_by=activated_by,
            evaluation_id=evaluation_id,
        )

    def get_activation_history(self, limit: int = 50) -> list[ModelActivationHistoryRow]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT model_id,
                       model_version,
                       action,
                       timestamp,
                       previous_model_id,
                       previous_model_version,
                       reason,
                       evaluation_id
                FROM model_activation_history
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ModelActivationHistoryRow(
                model_id=row[0],
                model_version=row[1],
                action=row[2],
                timestamp=row[3],
                previous_model_id=row[4],
                previous_model_version=row[5],
                reason=row[6],
                evaluation_id=row[7],
            )
            for row in rows
        ]

    def _ensure_schema(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS evaluation_runs (
                        evaluation_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        dataset_id TEXT NOT NULL,
                        eval_workers INTEGER NOT NULL,
                        total_models INTEGER NOT NULL,
                        completed_models INTEGER NOT NULL,
                        failed_models INTEGER NOT NULL,
                        started_at TEXT NOT NULL,
                        completed_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        evaluation_id TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        dataset_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        metrics_json TEXT NOT NULL,
                        error TEXT,
                        duration_ms INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(evaluation_id, model_id, model_version)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_evaluation_results__evaluation_id
                    ON evaluation_results(evaluation_id)
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS active_models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        activated_at TEXT NOT NULL,
                        activated_by TEXT NOT NULL,
                        evaluation_id TEXT,
                        is_active INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_active_models__is_active
                    ON active_models(is_active)
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS model_activation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        action TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        previous_model_id TEXT,
                        previous_model_version TEXT,
                        reason TEXT,
                        evaluation_id TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_model_activation_history__timestamp
                    ON model_activation_history(timestamp)
                    """
                )
                conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)


def _timestamp_now() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")
