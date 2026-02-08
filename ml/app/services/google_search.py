from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any, Callable
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from app.schemas.results import SearchResultItem


GOOGLE_SEARCH_URL = "https://customsearch.googleapis.com/customsearch/v1"


@dataclass(frozen=True)
class GoogleSearchConfig:
    api_key: str
    search_engine_id: str


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
    with urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


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
