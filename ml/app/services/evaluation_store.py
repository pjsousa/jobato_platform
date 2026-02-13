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
                conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)


def _timestamp_now() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")
