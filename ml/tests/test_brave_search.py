import logging

import pytest

from app.services.brave_search import (
    BraveSearchClient,
    BraveSearchConfig,
    DeterministicMockSearchClient,
)


def test_brave_search_calls_http_get_once_and_parses_results():
    calls: list[str] = []

    def http_get(url: str):
        calls.append(url)
        return {
            "web": {
                "results": [
                    {
                        "title": "Backend Engineer",
                        "description": "Remote role",
                        "url": "https://example.com/job",
                        "profile": {"name": "example.com"},
                    }
                ]
            }
        }

    client = BraveSearchClient(
        BraveSearchConfig(api_key="key", freshness="pm"),
        http_get=http_get,
        logger=logging.getLogger("test"),
    )

    results = client.search(run_id="run-1", search_query="site:example.com backend")

    assert len(results) == 1
    assert results[0].display_link == "example.com"
    assert len(calls) == 1


def test_brave_search_includes_freshness_in_url():
    calls: list[str] = []

    def http_get(url: str):
        calls.append(url)
        return {"web": {"results": []}}

    client = BraveSearchClient(
        BraveSearchConfig(api_key="key", freshness="pw"),
        http_get=http_get,
        logger=logging.getLogger("test"),
    )

    client.search(run_id="run-1", search_query="test query")

    assert len(calls) == 1
    assert "freshness=pw" in calls[0]


def test_brave_search_requires_run_id():
    client = BraveSearchClient(BraveSearchConfig(api_key="key"))

    with pytest.raises(ValueError):
        client.search(run_id="", search_query="site:example.com backend")


def test_brave_search_returns_empty_for_empty_query():
    client = BraveSearchClient(BraveSearchConfig(api_key="key"))

    results = client.search(run_id="run-1", search_query="")

    assert results == []


def test_brave_search_propagates_http_get_error():
    def http_get(_url: str):
        raise TimeoutError("timeout")

    client = BraveSearchClient(
        BraveSearchConfig(api_key="key"),
        http_get=http_get,
    )

    with pytest.raises(TimeoutError):
        client.search(run_id="run-1", search_query="site:example.com backend")


def test_brave_search_extracts_domain_from_url_when_profile_missing():
    def http_get(url: str):
        return {
            "web": {
                "results": [
                    {
                        "title": "Job Posting",
                        "description": "Great role",
                        "url": "https://careers.company.com/jobs/123",
                    }
                ]
            }
        }

    client = BraveSearchClient(
        BraveSearchConfig(api_key="key"),
        http_get=http_get,
        logger=logging.getLogger("test"),
    )

    results = client.search(run_id="run-1", search_query="test")

    assert len(results) == 1
    assert results[0].display_link == "careers.company.com"


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


def test_mock_search_client_requires_run_id():
    client = DeterministicMockSearchClient()

    with pytest.raises(ValueError):
        client.search(run_id="", search_query="test query")
