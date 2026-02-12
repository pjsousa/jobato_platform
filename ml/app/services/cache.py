from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os
from pathlib import Path
import sqlite3

import yaml


@dataclass(frozen=True)
class CachePolicy:
    ttl_hours: int
    revisit_throttle_days: int


@dataclass(frozen=True)
class CachedSearchResult:
    title: str
    snippet: str
    raw_url: str
    final_url: str
    domain: str


@dataclass(frozen=True)
class CachedSearchBundle:
    results: list[CachedSearchResult]
    cached_at: str
    cache_expires_at: str


class CacheService:
    def __init__(
        self,
        *,
        data_dir: Path | str | None = None,
        policy: CachePolicy,
        logger: logging.Logger | None = None,
    ) -> None:
        data_root = Path(data_dir or os.getenv("DATA_DIR", "data"))
        self._runs_dir = data_root / "db" / "runs"
        self._policy = policy
        self._logger = logger or logging.getLogger(__name__)

    def generate_cache_key(self, *, query_text: str, domain: str) -> str:
        normalized_query = " ".join(query_text.strip().lower().split())
        normalized_domain = domain.strip().lower()
        key_source = f"{normalized_query}|{normalized_domain}"
        return hashlib.md5(key_source.encode("utf-8")).hexdigest()

    def build_cache_window(self, *, now: datetime) -> tuple[str, str]:
        normalized_now = _normalize_datetime(now)
        expires = normalized_now + timedelta(hours=self._policy.ttl_hours)
        return _format_timestamp(normalized_now), _format_timestamp(expires)

    def is_cache_fresh(self, *, cached_at: str, cache_expires_at: str, now: datetime) -> bool:
        if not cached_at or not cache_expires_at:
            return False
        expiry = _parse_timestamp(cache_expires_at)
        if expiry is None:
            return False
        return _normalize_datetime(now) < expiry

    def get_fresh_results(self, *, cache_key: str, now: datetime) -> CachedSearchBundle | None:
        newest_match: tuple[datetime, Path, str, str, str] | None = None
        found_expired = False

        for db_path in self._iter_run_databases():
            latest_metadata = self._fetch_latest_cache_metadata(db_path=db_path, cache_key=cache_key)
            if latest_metadata is None:
                continue

            run_id, cached_at, cache_expires_at = latest_metadata
            cached_at_instant = _parse_timestamp(cached_at)
            if cached_at_instant is None:
                continue

            if not self.is_cache_fresh(cached_at=cached_at, cache_expires_at=cache_expires_at, now=now):
                found_expired = True
                continue

            if newest_match is None or cached_at_instant > newest_match[0]:
                newest_match = (cached_at_instant, db_path, run_id, cached_at, cache_expires_at)

        if newest_match is None:
            if found_expired:
                self._logger.info("cache.expired cache_key=%s", cache_key)
            else:
                self._logger.info("cache.miss cache_key=%s", cache_key)
            return None

        _, db_path, run_id, cached_at, cache_expires_at = newest_match
        cached_results = self._fetch_cached_results(db_path=db_path, run_id=run_id, cache_key=cache_key)
        if not cached_results:
            self._logger.info("cache.miss cache_key=%s", cache_key)
            return None

        self._logger.warning(
            "cache.hit cache_key=%s source_run_id=%s source_db=%s result_count=%s",
            cache_key,
            run_id,
            db_path.name,
            len(cached_results),
        )
        return CachedSearchBundle(
            results=cached_results,
            cached_at=cached_at,
            cache_expires_at=cache_expires_at,
        )

    def find_latest_last_seen(self, *, url: str) -> str | None:
        if not url:
            return None

        latest_seen_at: tuple[datetime, str] | None = None
        for db_path in self._iter_run_databases():
            row = self._query_one(
                db_path=db_path,
                sql=(
                    "SELECT last_seen_at "
                    "FROM run_items "
                    "WHERE (final_url = ? OR raw_url = ?) AND last_seen_at IS NOT NULL "
                    "ORDER BY last_seen_at DESC, id DESC "
                    "LIMIT 1"
                ),
                params=(url, url),
            )
            if row is None:
                continue
            seen_at = str(row[0])
            parsed_seen_at = _parse_timestamp(seen_at)
            if parsed_seen_at is None:
                continue
            if latest_seen_at is None or parsed_seen_at > latest_seen_at[0]:
                latest_seen_at = (parsed_seen_at, seen_at)

        if latest_seen_at is None:
            return None
        return latest_seen_at[1]

    def is_revisit_throttled(self, *, last_seen_at: str | None, now: datetime) -> bool:
        if not last_seen_at:
            return False
        parsed_last_seen = _parse_timestamp(last_seen_at)
        if parsed_last_seen is None:
            return False
        revisit_available_at = parsed_last_seen + timedelta(days=self._policy.revisit_throttle_days)
        return _normalize_datetime(now) < revisit_available_at

    def _fetch_latest_cache_metadata(self, *, db_path: Path, cache_key: str) -> tuple[str, str, str] | None:
        row = self._query_one(
            db_path=db_path,
            sql=(
                "SELECT run_id, cached_at, cache_expires_at "
                "FROM run_items "
                "WHERE cache_key = ? AND cached_at IS NOT NULL AND cache_expires_at IS NOT NULL "
                "ORDER BY cached_at DESC, id DESC "
                "LIMIT 1"
            ),
            params=(cache_key,),
        )
        if row is None:
            return None
        return str(row[0]), str(row[1]), str(row[2])

    def _fetch_cached_results(self, *, db_path: Path, run_id: str, cache_key: str) -> list[CachedSearchResult]:
        rows = self._query_all(
            db_path=db_path,
            sql=(
                "SELECT title, snippet, raw_url, final_url, domain "
                "FROM run_items "
                "WHERE run_id = ? AND cache_key = ? "
                "ORDER BY id ASC"
            ),
            params=(run_id, cache_key),
        )
        results: list[CachedSearchResult] = []
        for row in rows:
            results.append(
                CachedSearchResult(
                    title=str(row[0]),
                    snippet=str(row[1]),
                    raw_url=str(row[2]),
                    final_url=str(row[3]),
                    domain=str(row[4]),
                )
            )
        return results

    def _iter_run_databases(self) -> list[Path]:
        if not self._runs_dir.exists():
            return []
        return sorted(self._runs_dir.glob("*.db"), key=lambda path: path.stat().st_mtime, reverse=True)

    def _query_one(self, *, db_path: Path, sql: str, params: tuple[object, ...]) -> tuple[object, ...] | None:
        rows = self._query_all(db_path=db_path, sql=sql, params=params)
        if not rows:
            return None
        return rows[0]

    def _query_all(self, *, db_path: Path, sql: str, params: tuple[object, ...]) -> list[tuple[object, ...]]:
        if not db_path.exists():
            return []
        try:
            connection = sqlite3.connect(db_path)
            try:
                cursor = connection.cursor()
                cursor.execute(sql, params)
                return list(cursor.fetchall())
            finally:
                connection.close()
        except sqlite3.Error:
            return []


def load_cache_policy(*, path: Path | None = None, config_dir: Path | None = None) -> CachePolicy:
    config_path = _resolve_cache_config_path(path=path, config_dir=config_dir)
    if not config_path.exists():
        raise ValueError(f"Cache config not found: {config_path}")

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid cache.yaml format: expected a map at root")

    cache_node = payload.get("cache")
    if not isinstance(cache_node, dict):
        raise ValueError("Invalid cache.yaml format: cache must be a map")

    ttl_hours = _read_positive_int(cache_node, "ttlHours")
    revisit_days = _read_positive_int(cache_node, "revisitThrottleDays")
    return CachePolicy(ttl_hours=ttl_hours, revisit_throttle_days=revisit_days)


def _resolve_cache_config_path(*, path: Path | None, config_dir: Path | None) -> Path:
    if path is not None:
        return path
    root = config_dir or Path(os.getenv("CONFIG_DIR", "config"))
    return Path(root) / "cache.yaml"


def _read_positive_int(node: dict[str, object], key: str) -> int:
    value = node.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Invalid cache.yaml format: {key} must be an integer")
    if value <= 0:
        raise ValueError(f"Invalid cache.yaml format: {key} must be greater than zero")
    return value


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return _normalize_datetime(parsed)


def _format_timestamp(value: datetime) -> str:
    normalized = _normalize_datetime(value).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")
