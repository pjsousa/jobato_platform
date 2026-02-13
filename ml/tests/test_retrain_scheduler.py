from __future__ import annotations

from datetime import datetime, timezone

from app.services.retrain_scheduler import DailyRetrainScheduler, parse_daily_schedule


def test_parse_daily_schedule_supports_standard_daily_cron() -> None:
    schedule = parse_daily_schedule("15 6 * * *")
    assert schedule.minute == 15
    assert schedule.hour == 6


def test_scheduler_triggers_once_when_due() -> None:
    trigger_count = 0

    def trigger() -> None:
        nonlocal trigger_count
        trigger_count += 1

    scheduler = DailyRetrainScheduler(
        trigger=trigger,
        schedule="0 6 * * *",
        enabled=True,
        now_provider=lambda: datetime(2026, 2, 13, 5, 0, tzinfo=timezone.utc),
    )

    triggered = scheduler.trigger_if_due(now=datetime(2026, 2, 13, 6, 0, tzinfo=timezone.utc))
    assert triggered is True
    assert trigger_count == 1

    not_triggered = scheduler.trigger_if_due(now=datetime(2026, 2, 13, 6, 0, tzinfo=timezone.utc))
    assert not_triggered is False
    assert trigger_count == 1


def test_scheduler_does_not_trigger_when_disabled() -> None:
    trigger_count = 0

    def trigger() -> None:
        nonlocal trigger_count
        trigger_count += 1

    scheduler = DailyRetrainScheduler(
        trigger=trigger,
        schedule="0 6 * * *",
        enabled=False,
        now_provider=lambda: datetime(2026, 2, 13, 5, 0, tzinfo=timezone.utc),
    )

    triggered = scheduler.trigger_if_due(now=datetime(2026, 2, 13, 6, 0, tzinfo=timezone.utc))
    assert triggered is False
    assert trigger_count == 0
