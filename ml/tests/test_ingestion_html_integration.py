from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.results import SearchResultItem


def test_ingest_run_with_html_storage(tmp_path):
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend Remote",
            domain="example.com",
            search_query="site:example.com Backend Remote",
        ),
    ]

    class StubSearchClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def search(self, *, run_id: str, search_query: str):
            self.calls.append((run_id, search_query))
            return [
                SearchResultItem(
                    title="Test Job",
                    snippet="Test snippet",
                    link="mock://example.com/job1",
                    display_link="example.com"
                )
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            batched = list(results)
            self.results.extend(batched)
            return len(batched)

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
        data_dir=tmp_path,
        capture_html=True,
    )

    assert len(search_client.calls) == 1
    assert outcome.issued_calls == 1
    assert outcome.persisted_results == 1
    assert len(writer.results) == 1

    result = writer.results[0]
    assert result.raw_html_path is not None
    assert Path(result.raw_html_path).exists()
    assert result.visible_text is not None
    assert "Mock result for example.com" in result.visible_text
    assert result.fetch_error is None
    assert result.extract_error is None


def test_ingest_run_with_html_fetch_error_continues_other_results(tmp_path):
    run_inputs = [
        RunInput(
            query_id="q1",
            query_text="Backend Remote",
            domain="example.com",
            search_query="site:example.com Backend Remote",
        ),
    ]

    class StubSearchClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def search(self, *, run_id: str, search_query: str):
            self.calls.append((run_id, search_query))
            return [
                SearchResultItem(
                    title="Failing Job",
                    snippet="Will fail to fetch",
                    link="https://fail.example.com/job1",
                    display_link="example.com"
                ),
                SearchResultItem(
                    title="Working Job",
                    snippet="Will capture HTML",
                    link="mock://example.com/job2",
                    display_link="example.com"
                )
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            batched = list(results)
            self.results.extend(batched)
            return len(batched)

    def fake_fetch(_self, url: str, *, run_id: str):
        if "fail.example.com" in url:
            return None, "Connection timeout"
        destination = tmp_path / "html" / "raw" / run_id / "ok.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("<html><body>Working content</body></html>", encoding="utf-8")
        return str(destination), None

    search_client = StubSearchClient()
    resolver = StubResolver()
    writer = StubWriter()

    with patch("app.pipelines.ingestion.HtmlFetcher.fetch_html", side_effect=fake_fetch, autospec=True):
        outcome = ingest_run(
            run_id="run-123",
            run_inputs=run_inputs,
            search_client=search_client,
            url_resolver=resolver,
            result_writer=writer,
            now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
            data_dir=tmp_path,
            capture_html=True,
        )

    assert len(search_client.calls) == 1
    assert outcome.issued_calls == 1
    assert outcome.persisted_results == 2
    assert len(writer.results) == 2

    failed = next(result for result in writer.results if "fail.example.com" in result.raw_url)
    succeeded = next(result for result in writer.results if "mock://example.com/job2" == result.raw_url)

    assert failed.raw_html_path is None
    assert failed.fetch_error == "Connection timeout"
    assert failed.extract_error is None
    assert failed.visible_text is None

    assert succeeded.raw_html_path is not None
    assert Path(succeeded.raw_html_path).exists()
    assert succeeded.fetch_error is None
    assert succeeded.extract_error is None
    assert succeeded.visible_text == "Working content"


def test_ingest_run_stores_html_path_under_data_prefix_when_data_dir_is_data(tmp_path):
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
                    title="Test Job",
                    snippet="Test snippet",
                    link="mock://example.com/job3",
                    display_link="example.com",
                )
            ]

    class StubResolver:
        def resolve(self, url: str):
            return type("Resolved", (), {"status_code": 200, "final_url": url, "redirected": False})()

    class StubWriter:
        def __init__(self) -> None:
            self.results = []

        def write_all(self, results):
            batched = list(results)
            self.results.extend(batched)
            return len(batched)

    data_dir = tmp_path / "data"
    writer = StubWriter()

    ingest_run(
        run_id="run-xyz",
        run_inputs=run_inputs,
        search_client=StubSearchClient(),
        url_resolver=StubResolver(),
        result_writer=writer,
        now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
        data_dir=data_dir,
        capture_html=True,
    )

    assert len(writer.results) == 1
    persisted = writer.results[0]
    assert persisted.raw_html_path is not None
    assert persisted.raw_html_path.startswith("data/html/raw/run-xyz/")
    expected_file = data_dir.parent / persisted.raw_html_path
    assert expected_file.exists()
