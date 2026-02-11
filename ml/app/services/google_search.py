from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from app.schemas.results import SearchResultItem


GOOGLE_SEARCH_URL = "https://customsearch.googleapis.com/customsearch/v1"


@dataclass(frozen=True)
class GoogleSearchConfig:
    api_key: str
    search_engine_id: str


class SearchServiceError(RuntimeError):
    pass


class GoogleSearchClient:
    def __init__(
        self,
        config: GoogleSearchConfig,
        http_get: Callable[[str], dict[str, Any]] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._http_get = http_get or _default_http_get
        self._logger = logger or logging.getLogger(__name__)

    def search(self, *, run_id: str, search_query: str) -> list[SearchResultItem]:
        if not run_id:
            raise ValueError("run_id is required")
        if not search_query:
            return []
        url = _build_search_url(self._config, search_query)
        payload = self._http_get(url)
        results = _parse_results(payload)
        self._logger.info(
            "google_search.completed run_id=%s query=%s results=%s",
            run_id,
            search_query,
            len(results),
        )
        return results


def _build_search_url(config: GoogleSearchConfig, search_query: str) -> str:
    params = {
        "key": config.api_key,
        "cx": config.search_engine_id,
        "q": search_query,
    }
    return f"{GOOGLE_SEARCH_URL}?{urlencode(params)}"


def _default_http_get(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "jobato/1.0"})
    try:
        with urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as error:
        raise SearchServiceError(f"Google search request failed with status {error.code}") from error
    except (TimeoutError, URLError, OSError) as error:
        raise SearchServiceError("Google search request failed due to a network or timeout error") from error

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as error:
        raise SearchServiceError("Google search returned invalid JSON") from error
    if not isinstance(parsed, dict):
        raise SearchServiceError("Google search returned an unexpected payload shape")
    return parsed


class DeterministicMockSearchClient:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def search(self, *, run_id: str, search_query: str) -> list[SearchResultItem]:
        if not run_id:
            raise ValueError("run_id is required")
        if not search_query:
            return []

        domain = _extract_domain_from_search_query(search_query)
        query_hash = hashlib.sha256(search_query.encode("utf-8")).hexdigest()[:12]
        result = SearchResultItem(
            title=f"Mock result for {domain}",
            snippet=f"Deterministic mock hit for query '{search_query}'.",
            link=f"mock://{domain}/jobs/{query_hash}",
            display_link=domain,
        )
        self._logger.info(
            "google_search.mock_completed run_id=%s query=%s results=%s",
            run_id,
            search_query,
            1,
        )
        return [result]


def _parse_results(payload: dict[str, Any]) -> list[SearchResultItem]:
    if not isinstance(payload, dict):
        return []
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return []
    results: list[SearchResultItem] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", ""))
        snippet = str(item.get("snippet", ""))
        link = str(item.get("link", ""))
        display_link = str(item.get("displayLink", ""))
        if not display_link and link:
            display_link = _extract_domain(link)
        results.append(
            SearchResultItem(
                title=title,
                snippet=snippet,
                link=link,
                display_link=display_link,
            )
        )
    return results


def _extract_domain(link: str) -> str:
    parsed = urlparse(link)
    return parsed.netloc


def _extract_domain_from_search_query(search_query: str) -> str:
    first_token = search_query.strip().split(" ", maxsplit=1)[0]
    if first_token.startswith("site:"):
        candidate = first_token[len("site:") :].strip().lower()
        if candidate:
            return candidate
    return "example.com"
