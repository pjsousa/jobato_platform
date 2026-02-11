from datetime import datetime, timezone

from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.results import SearchResultItem
from app.services.fetcher import DeterministicMockUrlResolver, FetchResponse, ResolvedUrl, UrlResolver


def test_url_resolver_follows_single_redirect():
    calls: list[str] = []

    def http_fetch(url: str) -> FetchResponse:
        calls.append(url)
        if url == "https://example.com/original":
            return FetchResponse(status_code=302, headers={"location": "https://example.com/final"})
        return FetchResponse(status_code=200, headers={})

    resolver = UrlResolver(http_fetch=http_fetch)

    resolved = resolver.resolve("https://example.com/original")

    assert resolved.status_code == 200
    assert resolved.final_url == "https://example.com/final"
    assert resolved.redirected is True
    assert calls == ["https://example.com/original", "https://example.com/final"]


def test_ingest_run_skips_404_results():
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend Remote",
            domain="example.com",
            search_query="site:example.com Backend Remote",
        )
    ]

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return [
                SearchResultItem(
                    title="Role",
                    snippet="Snippet",
                    link="https://example.com/job",
                    display_link="example.com",
                )
            ]

    class StubResolver:
        def resolve(self, url: str):
            return ResolvedUrl(status_code=404, final_url=url, redirected=False)

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    writer = StubWriter()
    outcome = ingest_run(
        run_id="run-404",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=writer,
        now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert outcome.skipped_404 == 1
    assert outcome.persisted_results == 0
    assert writer.results == []


def test_deterministic_mock_url_resolver_redirects_once():
    resolver = DeterministicMockUrlResolver()

    resolved = resolver.resolve("https://example.com/redirect/job")

    assert resolved.redirected is True
    assert resolved.status_code == 200
    assert resolved.final_url == "https://example.com/final/job"
