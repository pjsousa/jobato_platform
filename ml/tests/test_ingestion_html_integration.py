import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.results import ResultMetadata


def test_ingest_run_with_html_storage():
    """Test ingestion pipeline with HTML fetching and storage"""
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
            # Return a mock result
            from app.schemas.results import SearchResultItem
            return [
                SearchResultItem(
                    title="Test Job",
                    snippet="Test snippet",
                    link="http://example.com/job1",
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
            self.results.extend(list(results))
            return len(self.results)

    # Test with temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        search_client = StubSearchClient()
        resolver = StubResolver()
        writer = StubWriter()
        
        # Mock the HTML fetcher to return a fixed file path
        with patch('app.pipelines.ingestion.HtmlFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_html.return_value = (f"{tmp_dir}/test.html", None)
            mock_fetcher_class.return_value = mock_fetcher
            
            # Mock the HTML extractor to return test text
            with patch('app.pipelines.ingestion.HtmlExtractor') as mock_extractor_class:
                mock_extractor = MagicMock()
                mock_extractor.extract_visible_text.return_value = ("Test visible text", None)
                mock_extractor_class.return_value = mock_extractor

                outcome = ingest_run(
                    run_id="run-123",
                    run_inputs=run_inputs,
                    search_client=search_client,
                    url_resolver=resolver,
                    result_writer=writer,
                    now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
                    data_dir=tmp_dir
                )

                # Verify
                assert len(search_client.calls) == 1
                assert outcome.issued_calls == 1
                assert len(writer.results) == 1
                
                result = writer.results[0]
                assert result.raw_html_path is not None
                assert result.visible_text == "Test visible text"
                assert result.fetch_error is None
                assert result.extract_error is None


def test_ingest_run_with_html_fetch_error():
    """Test ingestion pipeline with HTML fetch error handling"""
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
            # Return a mock result
            from app.schemas.results import SearchResultItem
            return [
                SearchResultItem(
                    title="Test Job",
                    snippet="Test snippet",
                    link="http://example.com/job1",
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
            self.results.extend(list(results))
            return len(self.results)

    # Test with temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        search_client = StubSearchClient()
        resolver = StubResolver()
        writer = StubWriter()
        
        # Mock the HTML fetcher to return an error
        with patch('app.pipelines.ingestion.HtmlFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_html.return_value = (None, "Connection timeout")
            mock_fetcher_class.return_value = mock_fetcher

            outcome = ingest_run(
                run_id="run-123",
                run_inputs=run_inputs,
                search_client=search_client,
                url_resolver=resolver,
                result_writer=writer,
                now=datetime(2026, 2, 8, 12, 0, tzinfo=timezone.utc),
                data_dir=tmp_dir
            )

            # Verify
            assert len(search_client.calls) == 1
            assert outcome.issued_calls == 1
            assert len(writer.results) == 1
            
            result = writer.results[0]
            assert result.raw_html_path is None
            assert result.fetch_error == "Connection timeout"
            assert result.extract_error is None