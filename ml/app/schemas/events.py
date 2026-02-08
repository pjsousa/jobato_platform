from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def build_run_event(
    *,
    event_type: str,
    run_id: str,
    payload: dict[str, Any],
    event_version: int = 1,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    if not event_type or event_type != event_type.lower() or "." not in event_type:
        raise ValueError("event_type must be dot-lowercase")

    event_time = occurred_at or datetime.now(timezone.utc)
    return {
        "eventId": event_id or str(uuid4()),
        "eventType": event_type,
        "eventVersion": event_version,
        "occurredAt": _format_timestamp(event_time),
        "runId": run_id,
        "payload": payload,
    }


def _format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")
