from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import select

from app.db.models import RunResult
from app.db.results_repository import ResultRepository
from app.db.session import open_session
from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.results import ResultMetadata, SearchResultItem
from app.services.cache import CachePolicy, CacheService


def test_ingest_run_short_circuits_external_search_on_fresh_cache(tmp_path):
    data_dir = tmp_path / "data"
    policy = CachePolicy(ttl_hours=12, revisit_throttle_days=7)
    cache_service = CacheService(data_dir=data_dir, policy=policy)
    now = datetime(2026, 2, 12, 12, 0, 0, tzinfo=timezone.utc)

    run_input = RunInput(
        query_id="q1",
        query_text="staff backend remote",
        domain="workable.com",
        search_query="site:workable.com staff backend remote",
    )
    cache_key = cache_service.generate_cache_key(query_text=run_input.query_text, domain=run_input.domain)
    _seed_cached_result(
        data_dir=data_dir,
        run_id="run-a",
        run_input=run_input,
        cache_key=cache_key,
        cached_at=_format_timestamp(now - timedelta(hours=1)),
        cache_expires_at=_format_timestamp(now + timedelta(hours=11)),
        last_seen_at=_format_timestamp(now - timedelta(days=10)),
    )

    search_calls: list[tuple[str, str]] = []
    resolver_calls: list[str] = []

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            search_calls.append((run_id, search_query))
            return []

    class StubResolver:
        def resolve(self, url: str):
            resolver_calls.append(url)
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    outcome = ingest_run(
        run_id="run-b",
        run_inputs=[run_input],
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        now=now,
        data_dir=data_dir,
        cache_policy=policy,
        cache_service=cache_service,
    )

    persisted = _read_run_results(data_dir=data_dir, run_id="run-b")

    assert outcome.issued_calls == 0
    assert len(search_calls) == 0
    assert len(resolver_calls) == 0
    assert len(persisted) == 1
    assert persisted[0].cache_key == cache_key
    assert persisted[0].cached_at is not None
    assert persisted[0].cache_expires_at is not None


def test_ingest_run_calls_search_when_cache_expires_on_boundary(tmp_path):
    data_dir = tmp_path / "data"
    policy = CachePolicy(ttl_hours=12, revisit_throttle_days=7)
    cache_service = CacheService(data_dir=data_dir, policy=policy)
    now = datetime(2026, 2, 12, 12, 0, 0, tzinfo=timezone.utc)

    run_input = RunInput(
        query_id="q1",
        query_text="staff backend remote",
        domain="workable.com",
        search_query="site:workable.com staff backend remote",
    )
    cache_key = cache_service.generate_cache_key(query_text=run_input.query_text, domain=run_input.domain)
    _seed_cached_result(
        data_dir=data_dir,
        run_id="run-a",
        run_input=run_input,
        cache_key=cache_key,
        cached_at=_format_timestamp(now - timedelta(hours=12)),
        cache_expires_at=_format_timestamp(now),
        last_seen_at=_format_timestamp(now - timedelta(days=10)),
    )

    search_calls: list[tuple[str, str]] = []

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            search_calls.append((run_id, search_query))
            return [
                SearchResultItem(
                    title="Fresh Result",
                    snippet="Live search result",
                    link="mock://workable.com/jobs/new-result",
                    display_link="workable.com",
                )
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    outcome = ingest_run(
        run_id="run-b",
        run_inputs=[run_input],
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        now=now,
        data_dir=data_dir,
        cache_policy=policy,
        cache_service=cache_service,
    )

    persisted = _read_run_results(data_dir=data_dir, run_id="run-b")

    assert len(search_calls) == 1
    assert outcome.issued_calls == 1
    assert len(persisted) == 1
    assert persisted[0].cache_key == cache_key


def test_ingest_run_applies_revisit_throttle_before_html_fetch(tmp_path):
    data_dir = tmp_path / "data"
    policy = CachePolicy(ttl_hours=12, revisit_throttle_days=7)
    cache_service = CacheService(data_dir=data_dir, policy=policy)
    now = datetime(2026, 2, 12, 12, 0, 0, tzinfo=timezone.utc)

    run_input = RunInput(
        query_id="q1",
        query_text="staff backend remote",
        domain="workable.com",
        search_query="site:workable.com staff backend remote",
    )
    cache_key = cache_service.generate_cache_key(query_text=run_input.query_text, domain=run_input.domain)
    _seed_cached_result(
        data_dir=data_dir,
        run_id="run-a",
        run_input=run_input,
        cache_key=cache_key,
        cached_at=_format_timestamp(now - timedelta(hours=1)),
        cache_expires_at=_format_timestamp(now + timedelta(hours=11)),
        last_seen_at=_format_timestamp(now - timedelta(days=1)),
    )

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return []

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    with patch(
        "app.pipelines.ingestion.HtmlFetcher.fetch_html",
        side_effect=AssertionError("HTML fetch must be skipped when revisit throttle applies"),
    ):
        ingest_run(
            run_id="run-b",
            run_inputs=[run_input],
            search_client=StubSearchClient(),
            url_resolver=StubResolver(),
            now=now,
            data_dir=data_dir,
            capture_html=True,
            cache_policy=policy,
            cache_service=cache_service,
        )

    persisted = _read_run_results(data_dir=data_dir, run_id="run-b")

    assert len(persisted) == 1
    assert persisted[0].skip_reason == "revisit_throttle"
    assert persisted[0].raw_html_path is None


def _seed_cached_result(
    *,
    data_dir: Path,
    run_id: str,
    run_input: RunInput,
    cache_key: str,
    cached_at: str,
    cache_expires_at: str,
    last_seen_at: str,
) -> None:
    db_path = data_dir / "db" / "runs" / f"{run_id}.db"
    session = open_session(db_path)
    repository = ResultRepository(session)
    repository.write_all(
        [
            ResultMetadata(
                run_id=run_id,
                query_id=run_input.query_id,
                query_text=run_input.query_text,
                search_query=run_input.search_query,
                domain=run_input.domain,
                title="Cached title",
                snippet="Cached snippet",
                raw_url="mock://workable.com/jobs/cached-result",
                final_url="mock://workable.com/jobs/cached-result",
                created_at=datetime(2026, 2, 12, 11, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 2, 12, 11, 0, 0, tzinfo=timezone.utc),
                cache_key=cache_key,
                cached_at=cached_at,
                cache_expires_at=cache_expires_at,
                last_seen_at=last_seen_at,
            )
        ]
    )
    session.close()


def _read_run_results(*, data_dir: Path, run_id: str) -> list[RunResult]:
    db_path = data_dir / "db" / "runs" / f"{run_id}.db"
    session = open_session(db_path)
    try:
        return list(session.execute(select(RunResult).where(RunResult.run_id == run_id)).scalars().all())
    finally:
        session.close()


def _format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")
