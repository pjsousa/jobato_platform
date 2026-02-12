from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError


@dataclass(frozen=True)
class FetchResponse:
    status_code: int
    headers: dict[str, str]


@dataclass(frozen=True)
class ResolvedUrl:
    status_code: int
    final_url: str
    redirected: bool


class FetcherError(RuntimeError):
    pass


class UrlResolver:
    def __init__(self, http_fetch: Callable[[str], FetchResponse] | None = None) -> None:
        self._http_fetch = http_fetch or _default_fetch

    def resolve(self, url: str) -> ResolvedUrl:
        if not url:
            raise ValueError("url is required")
        first = self._http_fetch(url)
        if _is_redirect(first.status_code):
            location = _get_location(first.headers)
            if location:
                target = urljoin(url, location)
                second = self._http_fetch(target)
                return ResolvedUrl(
                    status_code=second.status_code,
                    final_url=target,
                    redirected=True,
                )
        return ResolvedUrl(
            status_code=first.status_code,
            final_url=url,
            redirected=False,
        )


class DeterministicMockUrlResolver:
    def resolve(self, url: str) -> ResolvedUrl:
        if not url:
            raise ValueError("url is required")
        if "404" in url or "not-found" in url:
            return ResolvedUrl(status_code=404, final_url=url, redirected=False)
        if "/redirect/" in url:
            target = url.replace("/redirect/", "/final/", 1)
            return ResolvedUrl(status_code=200, final_url=target, redirected=True)
        return ResolvedUrl(status_code=200, final_url=url, redirected=False)


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _default_fetch(url: str) -> FetchResponse:
    opener = build_opener(_NoRedirectHandler())
    request = Request(url, headers={"User-Agent": "jobato/1.0"}, method="GET")
    try:
        response = opener.open(request, timeout=10)
    except HTTPError as error:
        return FetchResponse(status_code=error.code, headers=_normalize_headers(error.headers))
    except (TimeoutError, URLError, OSError) as error:
        raise FetcherError("Failed to resolve URL due to a network or timeout error") from error
    return FetchResponse(status_code=response.status, headers=_normalize_headers(response.headers))


def _normalize_headers(headers) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in headers.items():
        normalized[key.lower()] = value
    return normalized


def _get_location(headers: dict[str, str]) -> str | None:
    return headers.get("location")


def _is_redirect(status_code: int) -> bool:
    return 300 <= status_code < 400
