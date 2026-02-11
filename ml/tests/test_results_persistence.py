from datetime import datetime, timezone

from sqlalchemy import select

from app.db.models import RunResult
from app.db.results_repository import ResultRepository
from app.db.session import open_session
from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.results import SearchResultItem


def test_ingest_run_persists_results_linked_to_run(tmp_path):
    db_path = tmp_path / "run-results.db"
    session = open_session(db_path)
    repository = ResultRepository(session)

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return [
                SearchResultItem(
                    title="Backend Engineer",
                    snippet="Remote role",
                    link="https://example.com/job",
                    display_link="example.com",
                )
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    ingest_run(
        run_id="run-999",
        run_inputs=[
            RunInput(
                query_id="q1",
                query_text="Backend Remote",
                domain="example.com",
                search_query="site:example.com Backend Remote",
            )
        ],
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=repository,
        now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
    )

    results = session.execute(select(RunResult)).scalars().all()
    session.close()

    assert len(results) == 1
    persisted = results[0]
    assert persisted.run_id == "run-999"
    assert persisted.query_id == "q1"
    assert persisted.query_text == "Backend Remote"
    assert persisted.search_query == "site:example.com Backend Remote"
    assert persisted.domain == "example.com"
    assert persisted.title == "Backend Engineer"
    assert persisted.snippet == "Remote role"
    assert persisted.raw_url == "https://example.com/job"
    assert persisted.final_url == "https://example.com/job"
    assert persisted.created_at == "2026-02-08T12:00:00Z"
    assert persisted.updated_at == "2026-02-08T12:00:00Z"
