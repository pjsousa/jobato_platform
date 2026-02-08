from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, func, insert, select, update


@dataclass(frozen=True)
class ResetPolicy:
    time_zone: str
    reset_hour: int


@dataclass(frozen=True)
class QuotaConfig:
    daily_limit: int
    concurrency_limit: int
    reset_policy: ResetPolicy


class QuotaStore:
    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(
            f"sqlite:///{self._db_path}",
            future=True,
            connect_args={"check_same_thread": False},
        )
        self._metadata = MetaData()
        self._usage = Table(
            "quota_usage",
            self._metadata,
            Column("day", String, primary_key=True),
            Column("run_id", String, primary_key=True),
            Column("count", Integer, nullable=False),
        )
        self._metadata.create_all(self._engine)
        self._lock = threading.Lock()

    def get_daily_usage(self, day: str) -> int:
        with self._engine.begin() as conn:
            result = conn.execute(
                select(func.sum(self._usage.c.count)).where(self._usage.c.day == day)
            ).scalar()
        return int(result or 0)

    def increment_usage(self, day: str, run_id: str, count: int = 1) -> None:
        if count <= 0:
            return
        with self._lock:
            with self._engine.begin() as conn:
                existing = conn.execute(
                    select(self._usage.c.count).where(
                        (self._usage.c.day == day) & (self._usage.c.run_id == run_id)
                    )
                ).scalar()
                if existing is None:
                    conn.execute(
                        insert(self._usage).values(day=day, run_id=run_id, count=count)
                    )
                else:
                    conn.execute(
                        update(self._usage)
                        .where((self._usage.c.day == day) & (self._usage.c.run_id == run_id))
                        .values(count=int(existing) + count)
                    )


def load_quota_config(*, path: Path | None = None, config_dir: Path | None = None) -> QuotaConfig:
    config_path = _resolve_config_path(path, config_dir)
    payload = json.loads(config_path.read_text())

    if not isinstance(payload, dict):
        raise ValueError("Invalid quota.yaml format: expected a map at root")

    quota_node = payload.get("quota")
    if not isinstance(quota_node, dict):
        raise ValueError("Invalid quota.yaml format: quota must be a map")

    daily_limit = _read_int(quota_node, "dailyLimit")
    concurrency_limit = _read_int(quota_node, "concurrencyLimit")
    reset_policy_node = quota_node.get("resetPolicy")
    if not isinstance(reset_policy_node, dict):
        raise ValueError("Invalid quota.yaml format: resetPolicy must be a map")
    time_zone = _read_str(reset_policy_node, "timeZone")
    reset_hour = _read_int(reset_policy_node, "resetHour")

    _validate_limits(daily_limit, concurrency_limit, reset_hour, time_zone)

    return QuotaConfig(
        daily_limit=daily_limit,
        concurrency_limit=concurrency_limit,
        reset_policy=ResetPolicy(time_zone=time_zone, reset_hour=reset_hour),
    )


def _resolve_config_path(path: Path | None, config_dir: Path | None) -> Path:
    if path is not None:
        return path
    base_dir = config_dir or Path(os.getenv("CONFIG_DIR", "config"))
    return Path(base_dir).resolve() / "quota.yaml"


def _read_int(node: dict[str, object], key: str) -> int:
    value = node.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Invalid quota.yaml format: {key} must be an integer")
    return value


def _read_str(node: dict[str, object], key: str) -> str:
    value = node.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Invalid quota.yaml format: {key} must be a string")
    return value


def _validate_limits(daily_limit: int, concurrency_limit: int, reset_hour: int, time_zone: str) -> None:
    if daily_limit <= 0:
        raise ValueError("dailyLimit must be greater than zero")
    if concurrency_limit <= 0:
        raise ValueError("concurrencyLimit must be greater than zero")
    if reset_hour < 0 or reset_hour > 23:
        raise ValueError("resetHour must be between 0 and 23")
    if not time_zone.strip():
        raise ValueError("timeZone must be provided")


def quota_day_for(moment: datetime, reset_policy: ResetPolicy) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    try:
        zone = ZoneInfo(reset_policy.time_zone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timeZone must be a valid IANA zone") from exc
    localized = moment.astimezone(zone)
    quota_date = localized.date()
    if localized.hour < reset_policy.reset_hour:
        quota_date = quota_date - timedelta(days=1)
    return quota_date.isoformat()
