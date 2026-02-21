import json
from pathlib import Path

from app.pipelines.ingestion import IngestionOutcome, ZeroResultObservation
from app.runtime.run_events_worker import (
    RunEventsWorker,
    _prepare_run_database,
    _resolve_active_db_path,
    _update_db_pointer,
)


class _FakeRedisClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, str]]] = []

    def xadd(self, stream_key: str, fields: dict[str, str]):
        self.messages.append((stream_key, fields))
        return "1-0"


def test_worker_publishes_summary_metrics_and_zero_results(monkeypatch, tmp_path: Path):
    fake_redis = _FakeRedisClient()
    worker = RunEventsWorker(redis_client=fake_redis, data_dir=tmp_path)

    monkeypatch.setattr(
        "app.runtime.run_events_worker._build_clients",
        lambda _provider, _logger: (object(), object()),
    )
    monkeypatch.setattr(
        "app.runtime.run_events_worker._prepare_run_database",
        lambda _run_id, _data_dir, _logger: None,
    )
    monkeypatch.setattr(
        "app.runtime.run_events_worker._update_db_pointer",
        lambda _db_path, _data_dir, _logger: None,
    )
    monkeypatch.setattr(
        "app.runtime.run_events_worker.ingest_run",
        lambda **_kwargs: IngestionOutcome(
            issued_calls=3,
            persisted_results=2,
            skipped_404=0,
            new_jobs_count=2,
            zero_results=[
                ZeroResultObservation(
                    query_text="senior AND remote",
                    domain="workable.com",
                    occurred_at="2026-02-12T10:00:00Z",
                )
            ],
        ),
    )

    worker._process_event(
        {
            "eventId": "event-1",
            "eventType": "run.requested",
            "eventVersion": "1",
            "occurredAt": "2026-02-12T10:00:00Z",
            "runId": "run-1",
            "payload": json.dumps(
                {
                    "runInputs": [
                        {
                            "queryId": "q1",
                            "queryText": "senior AND remote",
                            "domain": "workable.com",
                            "searchQuery": "site:workable.com senior AND remote",
                        }
                    ]
                }
            ),
        }
    )

    assert len(fake_redis.messages) == 1
    stream_key, fields = fake_redis.messages[0]
    assert stream_key == "ml:run-events"
    assert fields["eventType"] == "run.completed"
    payload = json.loads(fields["payload"])
    assert payload["newJobsCount"] == 2
    assert payload["relevantCount"] == 0
    assert payload["zeroResults"] == [
        {
            "queryText": "senior AND remote",
            "domain": "workable.com",
            "occurredAt": "2026-02-12T10:00:00Z",
        }
    ]


def test_resolve_active_db_path_returns_none_when_no_pointer_or_default(tmp_path: Path):
    result = _resolve_active_db_path(tmp_path)
    assert result is None


def test_resolve_active_db_path_falls_back_to_default(tmp_path: Path):
    default_db = tmp_path / "db" / "runs" / "active.db"
    default_db.parent.mkdir(parents=True, exist_ok=True)
    default_db.touch()

    result = _resolve_active_db_path(tmp_path)
    assert result == default_db


def test_resolve_active_db_path_uses_pointer(tmp_path: Path):
    pointer_db = tmp_path / "db" / "runs" / "some-run.db"
    pointer_db.parent.mkdir(parents=True, exist_ok=True)
    pointer_db.touch()

    pointer_file = tmp_path / "db" / "current-db.txt"
    pointer_file.write_text("db/runs/some-run.db", encoding="utf-8")

    result = _resolve_active_db_path(tmp_path)
    assert result == pointer_db


def test_resolve_active_db_path_ignores_nonexistent_pointer(tmp_path: Path):
    pointer_file = tmp_path / "db" / "current-db.txt"
    pointer_file.parent.mkdir(parents=True, exist_ok=True)
    pointer_file.write_text("db/runs/nonexistent.db", encoding="utf-8")

    result = _resolve_active_db_path(tmp_path)
    assert result is None


def test_prepare_run_database_creates_new_when_no_source(tmp_path: Path):
    import logging

    logger = logging.getLogger("test")
    run_id = "test-run-123"

    result = _prepare_run_database(run_id, tmp_path, logger)

    expected_path = tmp_path / "db" / "runs" / f"{run_id}.db"
    assert result == expected_path
    assert result.exists()


def test_prepare_run_database_copies_from_source(tmp_path: Path):
    import logging

    logger = logging.getLogger("test")

    source_db = tmp_path / "db" / "runs" / "active.db"
    source_db.parent.mkdir(parents=True, exist_ok=True)
    source_db.write_text("existing data", encoding="utf-8")

    pointer_file = tmp_path / "db" / "current-db.txt"
    pointer_file.write_text("db/runs/active.db", encoding="utf-8")

    run_id = "new-run-456"
    result = _prepare_run_database(run_id, tmp_path, logger)

    assert result.read_text() == "existing data"


def test_update_db_pointer_writes_relative_path(tmp_path: Path):
    import logging

    logger = logging.getLogger("test")

    new_db_path = tmp_path / "db" / "runs" / "new-run.db"
    new_db_path.parent.mkdir(parents=True, exist_ok=True)
    new_db_path.touch()

    _update_db_pointer(new_db_path, tmp_path, logger)

    pointer_file = tmp_path / "db" / "current-db.txt"
    assert pointer_file.exists()
    assert pointer_file.read_text(encoding="utf-8").strip() == "db/runs/new-run.db"
