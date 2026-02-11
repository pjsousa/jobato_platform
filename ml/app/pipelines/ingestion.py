from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import re
from typing import Iterable, Protocol
import yaml

from app.schemas.results import ResultMetadata, SearchResultItem
from app.db.results_repository import ResultRepository
from app.db.session import open_session
from app.services.html_fetcher import HtmlFetcher
from app.services.html_extractor import HtmlExtractor


@dataclass(frozen=True)
class QueryDefinition:
    id: str
    text: str
    enabled: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AllowlistEntry:
    domain: str
    enabled: bool


@dataclass(frozen=True)
class RunInput:
    query_id: str | None
    query_text: str
    domain: str
    search_query: str


@dataclass(frozen=True)
class IngestionOutcome:
    issued_calls: int
    persisted_results: int
    skipped_404: int


class SearchClient(Protocol):
    def search(self, *, run_id: str, search_query: str) -> list[SearchResultItem]:
        raise NotImplementedError


class UrlResolver(Protocol):
    def resolve(self, url: str):
        raise NotImplementedError


class ResultWriter(Protocol):
    def write_all(self, results: Iterable[ResultMetadata]) -> int:
        raise NotImplementedError


_WATERMARK = re.compile(r"\s+")
_DOMAIN_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
)


def build_run_inputs(*, config_dir: Path | None = None) -> list[RunInput]:
    config_root = Path(config_dir or os.getenv("CONFIG_DIR", "config"))
    queries = _normalize_enabled_queries(_load_queries(config_root / "queries.yaml"))
    domains = _normalize_enabled_domains(_load_allowlists(config_root / "allowlists.yaml"))

    run_inputs: list[RunInput] = []
    for query in queries:
        for domain in domains:
            run_inputs.append(
                RunInput(
                    query_id=query.id,
                    query_text=query.text,
                    domain=domain,
                    search_query=_build_search_query(domain, query.text),
                )
            )
    return run_inputs


def ingest_run(
    *,
    run_id: str,
    run_inputs: Iterable[RunInput],
    search_client: SearchClient,
    url_resolver: UrlResolver,
    result_writer: ResultWriter | None = None,
    now: datetime | None = None,
    data_dir: Path | str | None = None,
    capture_html: bool = False,
) -> IngestionOutcome:
    writer = result_writer
    session = None
    if writer is None:
        db_path = _resolve_run_db_path(run_id, data_dir)
        session = open_session(db_path)
        writer = ResultRepository(session)
    timestamp = now or datetime.now(timezone.utc)
    issued_calls = 0
    skipped_404 = 0
    pending_results: list[ResultMetadata] = []
    logger = logging.getLogger(__name__)

    html_fetcher = HtmlFetcher(data_dir) if capture_html else None
    html_extractor = HtmlExtractor() if capture_html else None

    for run_input in run_inputs:
        issued_calls += 1
        results = search_client.search(run_id=run_id, search_query=run_input.search_query)
        for result in results:
            resolved = url_resolver.resolve(result.link)
            if resolved.status_code == 404:
                skipped_404 += 1
                logger.info("ingestion.skip_404 run_id=%s url=%s", run_id, result.link)
                continue
            if not resolved.final_url:
                continue
            domain = result.display_link or run_input.domain

            raw_html_path = None
            visible_text = None
            fetch_error = None
            extract_error = None

            if html_fetcher is not None and html_extractor is not None and resolved.final_url:
                fetched_html_path = None
                try:
                    fetched_html_path, fetch_error = html_fetcher.fetch_html(resolved.final_url, run_id=run_id)
                except Exception as exception:
                    fetch_error = str(exception)

                if fetched_html_path:
                    raw_html_path = _normalize_html_path_for_storage(fetched_html_path, data_dir)

                if fetched_html_path and not fetch_error:
                    try:
                        with open(fetched_html_path, "r", encoding="utf-8", errors="replace") as f:
                            html_content = f.read()
                        visible_text, extract_error = html_extractor.extract_visible_text(html_content)
                    except Exception as exception:
                        extract_error = str(exception)

            pending_results.append(
                ResultMetadata(
                    run_id=run_id,
                    query_id=run_input.query_id,
                    query_text=run_input.query_text,
                    search_query=run_input.search_query,
                    domain=domain,
                    title=result.title,
                    snippet=result.snippet,
                    raw_url=result.link,
                    final_url=resolved.final_url,
                    created_at=timestamp,
                    updated_at=timestamp,
                    raw_html_path=raw_html_path,
                    visible_text=visible_text,
                    fetch_error=fetch_error,
                    extract_error=extract_error,
                )
            )

    try:
        persisted = writer.write_all(pending_results)
        return IngestionOutcome(
            issued_calls=issued_calls,
            persisted_results=persisted,
            skipped_404=skipped_404,
        )
    finally:
        if session is not None:
            session.close()


def _build_search_query(domain: str, query_text: str) -> str:
    return f"site:{domain} {query_text}"


def _resolve_run_db_path(run_id: str, data_dir: Path | str | None) -> Path:
    data_root = Path(data_dir or os.getenv("DATA_DIR", "data"))
    return data_root / "db" / "runs" / f"{run_id}.db"


def _normalize_html_path_for_storage(file_path: str, data_dir: Path | str | None) -> str:
    html_path = Path(file_path)
    data_root = Path(data_dir or os.getenv("DATA_DIR", "data"))

    if data_root.name != "data":
        return str(html_path)

    try:
        relative = html_path.resolve().relative_to(data_root.resolve())
    except ValueError:
        return str(html_path)

    return str(Path("data") / relative)


def _load_queries(path: Path) -> list[QueryDefinition]:
    items = _load_yaml_list(path, "queries")
    queries: list[QueryDefinition] = []
    for item in items:
        queries.append(
            QueryDefinition(
                id=str(item.get("id", "")),
                text=str(item.get("text", "")),
                enabled=bool(item.get("enabled", False)),
                created_at=str(item.get("createdAt", "")),
                updated_at=str(item.get("updatedAt", "")),
            )
        )
    return queries


def _load_allowlists(path: Path) -> list[AllowlistEntry]:
    items = _load_yaml_list(path, "allowlists")
    entries: list[AllowlistEntry] = []
    for item in items:
        enabled_value = item.get("enabled")
        enabled = True if enabled_value is None else bool(enabled_value)
        entries.append(
            AllowlistEntry(
                domain=str(item.get("domain", "")),
                enabled=enabled,
            )
        )
    return entries


def _normalize_enabled_queries(queries: list[QueryDefinition]) -> list[QueryDefinition]:
    deduped: dict[str, QueryDefinition] = {}
    for query in queries:
        if not query.enabled:
            continue
        canonical_text = _canonicalize_query_text(query.text)
        if not canonical_text:
            raise ValueError("Query text is required")
        normalized = canonical_text.lower()
        deduped.setdefault(
            normalized,
            QueryDefinition(
                id=query.id,
                text=canonical_text,
                enabled=True,
                created_at=query.created_at,
                updated_at=query.updated_at,
            ),
        )
    return list(deduped.values())


def _normalize_enabled_domains(entries: list[AllowlistEntry]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if not entry.enabled:
            continue
        normalized = _normalize_domain(entry.domain)
        if normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def _canonicalize_query_text(text: str) -> str:
    if text is None:
        return ""
    return _WATERMARK.sub(" ", text.strip())


def _normalize_domain(input_value: str) -> str:
    if input_value is None:
        raise ValueError("Domain is required")
    trimmed = input_value.strip().lower()
    if not trimmed:
        raise ValueError("Domain is required")
    if trimmed.endswith("."):
        trimmed = trimmed[:-1]
    if "://" in trimmed or "/" in trimmed or "\\" in trimmed or ":" in trimmed or "*" in trimmed:
        raise ValueError("Domain must not include scheme, path, port, or wildcard")
    if len(trimmed) > 253:
        raise ValueError("Domain is too long")
    if not _DOMAIN_PATTERN.match(trimmed):
        raise ValueError("Domain format is invalid")
    return trimmed


def _load_yaml_list(path: Path, root_key: str) -> list[dict[str, object]]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return []
    payload = yaml.safe_load(content)
    if payload is None:
        return []
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid YAML in {path}: expected mapping root")

    items = payload.get(root_key)
    if items is None:
        return []
    if not isinstance(items, list):
        raise ValueError(f"Invalid YAML in {path}: '{root_key}' must be a list")

    normalized: list[dict[str, object]] = []
    for item in items:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized
