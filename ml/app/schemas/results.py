from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SearchResultItem:
    title: str
    snippet: str
    link: str
    display_link: str


@dataclass(frozen=True)
class ResultMetadata:
    run_id: str
    query_id: str | None
    query_text: str
    search_query: str
    domain: str
    title: str
    snippet: str
    raw_url: str
    final_url: str
    created_at: datetime
    updated_at: datetime
    raw_html_path: str | None = None
    visible_text: str | None = None
    fetch_error: str | None = None
    extract_error: str | None = None
    cache_key: str | None = None
    cached_at: str | None = None
    cache_expires_at: str | None = None
    last_seen_at: str | None = None
    skip_reason: str | None = None
