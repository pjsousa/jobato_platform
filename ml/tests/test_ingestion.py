from datetime import datetime, timezone

from app.pipelines.ingestion import RunInput, build_run_inputs, ingest_run
from app.schemas.results import SearchResultItem


def test_build_run_inputs_loads_enabled_queries_and_domains(tmp_path):
    queries_path = tmp_path / "queries.yaml"
    allowlists_path = tmp_path / "allowlists.yaml"

    queries_path.write_text(
        "\n".join(
            [
                "queries:",
                "- {id: q1, text: Backend Remote, enabled: true, createdAt: '2026-02-01T00:00:00Z', updatedAt: '2026-02-01T00:00:00Z'}",
                "- {id: q2, text: backend remote, enabled: true, createdAt: '2026-02-02T00:00:00Z', updatedAt: '2026-02-02T00:00:00Z'}",
                "- {id: q3, text: disabled, enabled: false, createdAt: '2026-02-02T00:00:00Z', updatedAt: '2026-02-02T00:00:00Z'}",
                "",
            ]
        )
    )
    allowlists_path.write_text(
        "\n".join(
            [
                "allowlists:",
                "- domain: Example.COM",
                "  enabled: true",
                "- domain: example.com",
                "  enabled: true",
                "- domain: disabled.com",
                "  enabled: false",
                "",
            ]
        )
    )

    run_inputs = build_run_inputs(config_dir=tmp_path)

    assert len(run_inputs) == 1
    run_input = run_inputs[0]
    assert run_input.query_text == "Backend Remote"
    assert run_input.domain == "example.com"
    assert run_input.search_query == "site:example.com Backend Remote"


def test_ingest_run_calls_search_for_each_input_with_run_id():
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend Remote",
            domain="example.com",
            search_query="site:example.com Backend Remote",
        ),
        RunInput(
            query_id="q2",
            query_text="Python Remote",
            domain="jobs.example.com",
            search_query="site:jobs.example.com Python Remote",
        ),
    ]

    class StubSearchClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def search(self, *, run_id: str, search_query: str):
            self.calls.append((run_id, search_query))
            return []

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    search_client = StubSearchClient()
    resolver = StubResolver()
    writer = StubWriter()

    outcome = ingest_run(
        run_id="run-123",
        run_inputs=run_inputs,
        search_client=search_client,
        url_resolver=resolver,
        result_writer=writer,
        now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert len(search_client.calls) == len(run_inputs)
    assert all(run_id == "run-123" for run_id, _ in search_client.calls)
    assert outcome.issued_calls == len(run_inputs)
    assert outcome.new_jobs_count == 0
    assert writer.results == []


def test_ingest_run_tracks_zero_result_query_domain_context():
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="senior AND remote",
            domain="workable.com",
            search_query="site:workable.com senior AND remote",
        )
    ]

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return []

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def write_all(self, results):
            return len(list(results))

    outcome = ingest_run(
        run_id="run-456",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=StubWriter(),
        now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
    )

    assert outcome.issued_calls == 1
    assert outcome.new_jobs_count == 0
    assert outcome.persisted_results == 0
    assert len(outcome.zero_results) == 1
    zero_result = outcome.zero_results[0]
    assert zero_result.query_text == "senior AND remote"
    assert zero_result.domain == "workable.com"
    assert zero_result.occurred_at == "2026-02-08T12:00:00Z"


def test_ingest_run_normalizes_urls_for_results():
    """Test that ingested results have normalized_url set."""
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend Remote",
            domain="example.com",
            search_query="site:example.com Backend Remote",
        ),
    ]

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return [
                SearchResultItem(
                    title="Senior Backend Engineer",
                    snippet="Remote position",
                    link="https://EXAMPLE.COM/jobs/123?utm_source=google&fbclid=abc",
                    display_link="example.com",
                ),
            ]

    class StubResolver:
        def resolve(self, url: str):
            # Simulate following redirect to final URL
            return type(
                "Resolved",
                (),
                {
                    "status_code": 200,
                    "final_url": "https://EXAMPLE.COM/jobs/123?utm_source=google&fbclid=abc",
                    "redirected": False,
                },
            )()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    writer = StubWriter()

    outcome = ingest_run(
        run_id="run-norm-1",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=writer,
        now=datetime(2026, 2, 12, 12, 0, tzinfo=timezone.utc),
    )

    assert outcome.persisted_results == 1
    assert len(writer.results) == 1

    result = writer.results[0]
    # Raw URL should be preserved
    assert result.raw_url == "https://EXAMPLE.COM/jobs/123?utm_source=google&fbclid=abc"
    # Normalized URL should be lowercase, tracking params stripped
    assert result.normalized_url == "https://example.com/jobs/123"
    assert result.normalization_error is None


def test_ingest_run_equivalent_urls_get_same_normalized_key():
    """Test that URLs differing only by tracking params get same normalized key."""
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend",
            domain="example.com",
            search_query="site:example.com Backend",
        ),
    ]

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return [
                SearchResultItem(
                    title="Job 1",
                    snippet="Description 1",
                    link="https://example.com/job/123?utm_source=google",
                    display_link="example.com",
                ),
                SearchResultItem(
                    title="Job 2",
                    snippet="Description 2",
                    link="https://example.com/job/123?fbclid=xyz&ref=social",
                    display_link="example.com",
                ),
                SearchResultItem(
                    title="Job 3",
                    snippet="Description 3",
                    link="https://EXAMPLE.COM/job/123#apply",
                    display_link="example.com",
                ),
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    writer = StubWriter()

    ingest_run(
        run_id="run-equiv-1",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=writer,
        now=datetime(2026, 2, 12, 12, 0, tzinfo=timezone.utc),
    )

    # All three URLs should normalize to the same key
    normalized_urls = [r.normalized_url for r in writer.results]
    assert len(set(normalized_urls)) == 1
    assert normalized_urls[0] == "https://example.com/job/123"


def test_ingest_run_handles_malformed_url_gracefully():
    """Test that malformed URLs don't crash ingestion, but record error."""
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend",
            domain="example.com",
            search_query="site:example.com Backend",
        ),
    ]

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return [
                SearchResultItem(
                    title="Valid Job",
                    snippet="Good description",
                    link="https://example.com/job/valid",
                    display_link="example.com",
                ),
                SearchResultItem(
                    title="Invalid Job",
                    snippet="Bad URL",
                    link="not-a-valid-url",
                    display_link="example.com",
                ),
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    writer = StubWriter()

    # Should not raise
    outcome = ingest_run(
        run_id="run-malformed-1",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=writer,
        now=datetime(2026, 2, 12, 12, 0, tzinfo=timezone.utc),
    )

    # Both results should be persisted
    assert outcome.persisted_results == 2
    assert len(writer.results) == 2

    # Find the valid and invalid results
    valid_result = next(r for r in writer.results if "valid" in r.raw_url)
    invalid_result = next(r for r in writer.results if "not-a-valid" in r.raw_url)

    # Valid URL should have normalized_url
    assert valid_result.normalized_url == "https://example.com/job/valid"
    assert valid_result.normalization_error is None

    # Invalid URL should have error recorded, normalized_url is None
    assert invalid_result.normalized_url is None
    assert invalid_result.normalization_error is not None
    assert "scheme" in invalid_result.normalization_error.lower()


def test_ingest_run_uses_final_url_for_normalization():
    """Test that normalization uses final_url after redirect resolution."""
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend",
            domain="example.com",
            search_query="site:example.com Backend",
        ),
    ]

    class StubSearchClient:
        def search(self, *, run_id: str, search_query: str):
            return [
                SearchResultItem(
                    title="Job",
                    snippet="Description",
                    link="https://short.link/abc?utm_source=test",
                    display_link="short.link",
                ),
            ]

    class StubResolver:
        def resolve(self, url: str):
            # Simulate redirect to final destination
            return type(
                "Resolved",
                (),
                {
                    "status_code": 200,
                    "final_url": "https://EXAMPLE.COM/jobs/123?utm_campaign=promo",
                    "redirected": True,
                },
            )()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            self.results.extend(list(results))
            return len(self.results)

    writer = StubWriter()

    ingest_run(
        run_id="run-redirect-1",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=writer,
        now=datetime(2026, 2, 12, 12, 0, tzinfo=timezone.utc),
    )

    assert len(writer.results) == 1
    result = writer.results[0]

    # Raw URL should be the original link
    assert result.raw_url == "https://short.link/abc?utm_source=test"
    # Final URL should be the redirect destination
    assert result.final_url == "https://EXAMPLE.COM/jobs/123?utm_campaign=promo"
    # Normalized URL should be based on final_url, with tracking stripped
    assert result.normalized_url == "https://example.com/jobs/123"
