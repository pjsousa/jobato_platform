import logging

import pytest

from app.services.google_search import (
    DeterministicMockSearchClient,
    GoogleSearchClient,
    GoogleSearchConfig,
)


def test_google_search_calls_http_get_once_and_parses_results():
    calls: list[str] = []

    def http_get(url: str):
        calls.append(url)
        return {
            "items": [
                {
                    "title": "Backend Engineer",
                    "snippet": "Remote role",
                    "link": "https://example.com/job",
                    "displayLink": "example.com",
                }
            ]
        }

    client = GoogleSearchClient(
        GoogleSearchConfig(api_key="key", search_engine_id="cx"),
        http_get=http_get,
        logger=logging.getLogger("test"),
    )

    results = client.search(run_id="run-1", search_query="site:example.com backend")

    assert len(results) == 1
    assert results[0].display_link == "example.com"
    assert len(calls) == 1


def test_google_search_requires_run_id():
    client = GoogleSearchClient(GoogleSearchConfig(api_key="key", search_engine_id="cx"))

    with pytest.raises(ValueError):
        client.search(run_id="", search_query="site:example.com backend")


def test_google_search_propagates_http_get_error():
    def http_get(_url: str):
        raise TimeoutError("timeout")

    client = GoogleSearchClient(
        GoogleSearchConfig(api_key="key", search_engine_id="cx"),
        http_get=http_get,
    )

    with pytest.raises(TimeoutError):
        client.search(run_id="run-1", search_query="site:example.com backend")


def test_mock_search_client_is_deterministic():
    client = DeterministicMockSearchClient(logger=logging.getLogger("test"))

    first = client.search(run_id="run-1", search_query="site:example.com backend")
    second = client.search(run_id="run-2", search_query="site:example.com backend")

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].link == second[0].link
    assert first[0].display_link == "example.com"


def test_mock_search_client_returns_zero_results_for_and_queries():
    client = DeterministicMockSearchClient(logger=logging.getLogger("test"))

    results = client.search(
        run_id="run-3",
        search_query="site:workable.com senior AND remote AND python",
    )

    assert results == []
