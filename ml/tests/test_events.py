from datetime import datetime, timezone

import pytest

from app.schemas.events import build_run_event


def test_build_run_event_includes_required_fields():
    event = build_run_event(
        event_type="run.completed",
        run_id="run-123",
        payload={"entries": 12},
        event_id="event-123",
        occurred_at=datetime(2026, 2, 7, 12, 0, tzinfo=timezone.utc),
    )

    assert event["eventId"] == "event-123"
    assert event["eventType"] == "run.completed"
    assert event["eventVersion"] == 1
    assert event["occurredAt"] == "2026-02-07T12:00:00Z"
    assert event["runId"] == "run-123"
    assert event["payload"] == {"entries": 12}


def test_build_run_event_rejects_non_dot_lowercase_event_type():
    with pytest.raises(ValueError):
        build_run_event(event_type="RunCompleted", run_id="run-123", payload={})
