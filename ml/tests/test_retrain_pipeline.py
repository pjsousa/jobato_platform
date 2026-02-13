from __future__ import annotations

import sqlite3
from pathlib import Path

from app.pipelines.retrain import RetrainPipeline
from app.services.evaluation_store import EvaluationStore


class _TrainableModel:
    def __init__(self) -> None:
        self.was_fit = False

    def fit(self, X, y):
        self.was_fit = True
        return self

    def predict(self, X):
        return [0.9 for _ in X]


class _FailingModel:
    def fit(self, X, y):
        raise RuntimeError("boom")

    def predict(self, X):
        return [0.0 for _ in X]


class _Registry:
    def __init__(self, model):
        self._model = model

    def get_model(self, identifier: str):
        if identifier == "baseline":
            return self._model
        return None


def _write_pointer(data_dir: Path, run_db_path: Path) -> None:
    db_dir = data_dir / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    (db_dir / "current-db.txt").write_text(str(run_db_path), encoding="utf-8")


def _seed_run_items(db_path: Path, *, rows: list[tuple[str, str, str, float, str]]) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE run_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                snippet TEXT,
                domain TEXT,
                relevance_score REAL,
                scored_at TEXT,
                is_duplicate INTEGER
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO run_items (title, snippet, domain, relevance_score, scored_at, is_duplicate)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            rows,
        )
        conn.commit()


def test_retrain_pipeline_creates_new_version_and_promotes_active_model(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path / "evaluations.db")
    store.activate_model(
        model_id="baseline",
        model_version="1.0.0",
        activated_by="tester",
        action="activated",
    )

    data_dir = tmp_path / "data"
    run_db_path = tmp_path / "run.db"
    _write_pointer(data_dir, run_db_path)
    _seed_run_items(
        run_db_path,
        rows=[
            ("Role A", "python", "example.com", 1.0, "2026-02-13T08:00:00Z"),
            ("Role B", "retail", "example.com", -1.0, "2026-02-13T08:01:00Z"),
        ],
    )

    artifact_dir = tmp_path / "trained"
    pipeline = RetrainPipeline(
        store=store,
        registry=_Registry(_TrainableModel()),
        data_dir=data_dir,
        artifact_dir=artifact_dir,
    )

    result = pipeline.run_once(triggered_by="manual")

    assert result is not None
    assert result.status == "completed"
    assert result.new_version is not None
    assert result.new_version.startswith("1.0.0-")
    assert result.label_count == 2

    active = store.get_active_model()
    assert active is not None
    assert active.model_version == result.new_version

    artifacts = list(artifact_dir.glob("baseline_*.pkl"))
    assert len(artifacts) == 1


def test_retrain_failure_keeps_previous_active_model(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path / "evaluations.db")
    store.activate_model(
        model_id="baseline",
        model_version="2.0.0",
        activated_by="tester",
        action="activated",
    )

    data_dir = tmp_path / "data"
    run_db_path = tmp_path / "run.db"
    _write_pointer(data_dir, run_db_path)
    _seed_run_items(
        run_db_path,
        rows=[("Role A", "python", "example.com", 1.0, "2026-02-13T08:00:00Z")],
    )

    pipeline = RetrainPipeline(
        store=store,
        registry=_Registry(_FailingModel()),
        data_dir=data_dir,
        artifact_dir=tmp_path / "trained",
    )

    result = pipeline.run_once(triggered_by="manual")

    assert result is not None
    assert result.status == "failed"
    active = store.get_active_model()
    assert active is not None
    assert active.model_version == "2.0.0"
