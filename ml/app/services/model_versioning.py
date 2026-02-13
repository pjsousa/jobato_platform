from __future__ import annotations

from datetime import datetime, timezone


def generate_retrain_version(previous_version: str | None, *, now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d%H%M%S")
    base = (previous_version or "v0").strip() or "v0"
    return f"{base}-{timestamp}"
