from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, TypeVar

from app.services.quota import QuotaConfig, QuotaStore, quota_day_for
from app.schemas.events import build_run_event

RunInput = TypeVar("RunInput")


@dataclass(frozen=True)
class RunOutcome:
    status: str
    reason: str | None
    issued_calls: int


def run_pipeline(
    *,
    run_id: str,
    run_inputs: Iterable[RunInput],
    call_fn: Callable[[RunInput], None],
    quota_store: QuotaStore,
    quota_config: QuotaConfig,
    now: datetime | None = None,
    event_publisher: Callable[[dict[str, Any]], None] | None = None,
) -> RunOutcome:
    inputs = list(run_inputs)
    if not inputs:
        return RunOutcome(status="completed", reason=None, issued_calls=0)

    current_time = now or datetime.now(timezone.utc)
    quota_day = quota_day_for(current_time, quota_config.reset_policy)
    used = quota_store.get_daily_usage(quota_day)
    remaining = max(quota_config.daily_limit - used, 0)
    allowed_inputs = inputs[:remaining]

    def execute_item(item: RunInput) -> None:
        quota_store.increment_usage(quota_day, run_id)
        call_fn(item)

    if allowed_inputs:
        with ThreadPoolExecutor(max_workers=quota_config.concurrency_limit) as executor:
            futures = [executor.submit(execute_item, item) for item in allowed_inputs]
            for future in futures:
                future.result()

    status = "completed" if len(allowed_inputs) == len(inputs) else "partial"
    reason = None if status == "completed" else "quota-reached"
    outcome = RunOutcome(status=status, reason=reason, issued_calls=len(allowed_inputs))
    if event_publisher is not None:
        event_publisher(build_run_completion_event(run_id, outcome))
    return outcome


def build_run_completion_event(run_id: str, outcome: RunOutcome) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": outcome.status}
    if outcome.reason:
        payload["reason"] = outcome.reason
    return build_run_event(event_type="run.completed", run_id=run_id, payload=payload)
