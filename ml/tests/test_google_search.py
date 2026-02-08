import logging

import pytest

from app.services.google_search import GoogleSearchClient, GoogleSearchConfig


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
