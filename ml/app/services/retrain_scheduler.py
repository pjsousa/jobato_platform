from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Event, Thread
from typing import Callable


@dataclass(frozen=True)
class DailySchedule:
    minute: int
    hour: int


class DailyRetrainScheduler:
    def __init__(
        self,
        *,
        trigger: Callable[[], None],
        schedule: str = "0 6 * * *",
        enabled: bool = True,
        poll_interval_seconds: float = 30.0,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._trigger = trigger
        self._enabled = enabled
        self._poll_interval_seconds = poll_interval_seconds
        self._now_provider = now_provider or (lambda: datetime.now().astimezone())
        self._timezone = self._now_provider().astimezone().tzinfo or timezone.utc
        self._schedule = parse_daily_schedule(schedule)
        self._next_run_at = self.next_run_after(self._now_provider())
        self._stop_event = Event()
        self._thread: Thread | None = None

    @property
    def next_run_at(self) -> datetime:
        return self._next_run_at

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, name="daily-retrain-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def trigger_if_due(self, *, now: datetime | None = None) -> bool:
        if not self._enabled:
            return False
        current = (now or self._now_provider()).astimezone(self._timezone)
        if current < self._next_run_at:
            return False
        self._trigger()
        self._next_run_at = self.next_run_after(current + timedelta(minutes=1))
        return True

    def next_run_after(self, instant: datetime) -> datetime:
        current = instant.astimezone(self._timezone)
        candidate = current.replace(
            hour=self._schedule.hour,
            minute=self._schedule.minute,
            second=0,
            microsecond=0,
        )
        if candidate <= current:
            candidate = candidate + timedelta(days=1)
        return candidate

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self.trigger_if_due()
            self._stop_event.wait(self._poll_interval_seconds)


def parse_daily_schedule(value: str) -> DailySchedule:
    parts = value.split()
    if len(parts) != 5:
        raise ValueError("Schedule must use cron format 'M H * * *'")
    minute = int(parts[0])
    hour = int(parts[1])
    if parts[2:] != ["*", "*", "*"]:
        raise ValueError("Only daily cron schedules are supported")
    if minute < 0 or minute > 59:
        raise ValueError("Minute must be between 0 and 59")
    if hour < 0 or hour > 23:
        raise ValueError("Hour must be between 0 and 23")
    return DailySchedule(minute=minute, hour=hour)
