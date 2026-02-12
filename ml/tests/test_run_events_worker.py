import json
from pathlib import Path

from app.pipelines.ingestion import IngestionOutcome, ZeroResultObservation
from app.runtime.run_events_worker import RunEventsWorker


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
