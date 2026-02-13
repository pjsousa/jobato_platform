from __future__ import annotations

import sqlite3
from pathlib import Path

from app.pipelines.retrain import RetrainPipeline
from app.services.evaluation_store import EvaluationStore


class _Registry:
    def get_model(self, identifier: str):
        return None


def _prepare_empty_run_items(db_path: Path) -> None:
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
        conn.commit()


def test_no_labels_retrain_is_skipped_and_active_model_is_unchanged(tmp_path: Path) -> None:
    store = EvaluationStore(tmp_path / "evaluations.db")
    store.activate_model(
        model_id="baseline",
        model_version="3.0.0",
        activated_by="tester",
        action="activated",
    )

    data_dir = tmp_path / "data"
    db_dir = data_dir / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    run_db_path = tmp_path / "run.db"
    (db_dir / "current-db.txt").write_text(str(run_db_path), encoding="utf-8")
    _prepare_empty_run_items(run_db_path)

    pipeline = RetrainPipeline(
        store=store,
        registry=_Registry(),
        data_dir=data_dir,
        artifact_dir=tmp_path / "trained",
    )

    result = pipeline.run_once(triggered_by="manual")

    assert result is not None
    assert result.status == "skipped"
    assert result.new_version == "3.0.0"
    assert result.label_count == 0

    active = store.get_active_model()
    assert active is not None
    assert active.model_version == "3.0.0"
