from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, RunResult
from app.pipelines.scoring import score_run_results
from app.services.evaluation_store import EvaluationResultRow, EvaluationStore
from app.services.model_activation import ModelActivationService


class _FakeRegistry:
    def __init__(self, model_ids: set[str]) -> None:
        self._model_ids = model_ids

    def has_model(self, identifier: str) -> bool:
        return identifier in self._model_ids


class _PredictingModel:
    version = "runtime-version"

    def predict(self, X):
        return [0.42 for _ in X]


class _PredictingRegistry:
    is_initialized = True

    def get_model(self, identifier: str):
        if identifier == "model-a":
            return _PredictingModel()
        return None


def _seed_evaluation_result(store: EvaluationStore, *, evaluation_id: str, model_id: str, model_version: str):
    store.create_run(
        evaluation_id=evaluation_id,
        dataset_id="dataset-1",
        eval_workers=2,
        total_models=1,
    )
    store.store_result(
        EvaluationResultRow(
            evaluation_id=evaluation_id,
            model_id=model_id,
            model_version=model_version,
            dataset_id="dataset-1",
            status="completed",
            metrics={"precision": 0.8, "recall": 0.8, "f1": 0.8, "accuracy": 0.8},
            error=None,
            duration_ms=100,
            created_at="2026-02-13T10:00:00Z",
        )
    )


def test_activation_and_rollback_history(tmp_path):
    store = EvaluationStore(tmp_path / "evaluations.db")
    _seed_evaluation_result(store, evaluation_id="eval-a", model_id="model-a", model_version="1.0.0")
    _seed_evaluation_result(store, evaluation_id="eval-b", model_id="model-b", model_version="2.0.0")

    service = ModelActivationService(
        store=store,
        registry=_FakeRegistry({"model-a", "model-b"}),
    )

    first = service.activate_model(model_id="model-a", activated_by="tester")
    assert first.model_id == "model-a"
    assert service.get_active_model().model_id == "model-a"

    second = service.activate_model(model_id="model-b", activated_by="tester")
    assert second.model_id == "model-b"
    assert service.get_active_model().model_id == "model-b"

    rolled_back = service.rollback_model(model_id="model-a", activated_by="tester")
    assert rolled_back.model_id == "model-a"
    assert service.get_active_model().model_id == "model-a"

    history = service.history_payload()["history"]
    assert len(history) >= 3
    assert history[0]["action"] == "rollback"


def test_scoring_uses_active_model_version(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    evaluations_db = data_dir / "db" / "evaluations.db"
    store = EvaluationStore(evaluations_db)
    _seed_evaluation_result(store, evaluation_id="eval-a", model_id="model-a", model_version="9.9.9")
    store.activate_model(
        model_id="model-a",
        model_version="9.9.9",
        activated_by="tester",
        action="activated",
        evaluation_id="eval-a",
    )

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setattr("app.pipelines.scoring.get_registry", lambda: _PredictingRegistry())

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(
        RunResult(
            run_id="run-1",
            query_id="q1",
            query_text="python",
            search_query="site:example.com python",
            domain="example.com",
            title="Role",
            snippet="Desc",
            raw_url="https://example.com/1",
            final_url="https://example.com/1",
            created_at="2026-02-13T10:00:00Z",
            updated_at="2026-02-13T10:00:00Z",
            is_duplicate=False,
            is_hidden=False,
            duplicate_count=0,
        )
    )
    session.commit()

    outcome = score_run_results(session, "run-1")
    assert outcome.scored_count == 1

    row = session.query(RunResult).filter_by(run_id="run-1").one()
    assert row.relevance_score == 0.42
    assert row.score_version == "9.9.9"
    session.close()
