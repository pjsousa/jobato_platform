from datetime import datetime, timezone
import threading
import time

from app.pipelines.run_pipeline import build_run_completion_event, run_pipeline, RunOutcome
from app.services.quota import QuotaConfig, QuotaStore, ResetPolicy


def test_run_pipeline_enforces_concurrency_limit(tmp_path):
    db_path = tmp_path / "quota.db"
    store = QuotaStore(db_path)
    config = QuotaConfig(daily_limit=10, concurrency_limit=2, reset_policy=ResetPolicy("UTC", 0))

    active = 0
    max_active = 0
    lock = threading.Lock()

    def call_fn(item: int) -> None:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1

    run_pipeline(
        run_id="run-1",
        run_inputs=list(range(5)),
        call_fn=call_fn,
        quota_store=store,
        quota_config=config,
        now=datetime(2026, 2, 7, 12, 0, tzinfo=timezone.utc),
    )

    assert max_active <= 2


def test_run_pipeline_stops_when_quota_reached(tmp_path):
    db_path = tmp_path / "quota.db"
    store = QuotaStore(db_path)
    config = QuotaConfig(daily_limit=2, concurrency_limit=3, reset_policy=ResetPolicy("UTC", 0))

    calls: list[int] = []

    def call_fn(item: int) -> None:
        calls.append(item)

    outcome = run_pipeline(
        run_id="run-2",
        run_inputs=[1, 2, 3, 4],
        call_fn=call_fn,
        quota_store=store,
        quota_config=config,
        now=datetime(2026, 2, 7, 12, 0, tzinfo=timezone.utc),
    )

    assert calls == [1, 2]
    assert outcome.status == "partial"
    assert outcome.reason == "quota-reached"
    assert store.get_daily_usage("2026-02-07") == 2


def test_build_run_completion_event_includes_status_and_reason():
    outcome = RunOutcome(status="partial", reason="quota-reached", issued_calls=2)

    event = build_run_completion_event("run-9", outcome)

    assert event["eventType"] == "run.completed"
    assert event["runId"] == "run-9"
    assert event["payload"]["status"] == "partial"
    assert event["payload"]["reason"] == "quota-reached"
