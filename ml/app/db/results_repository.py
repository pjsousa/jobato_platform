from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy.orm import Session

from app.db.models import RunResult
from app.schemas.results import ResultMetadata


class ResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def write_all(self, results: Iterable[ResultMetadata]) -> int:
        rows = [self._to_row(result) for result in results]
        if not rows:
            return 0
        self._session.add_all(rows)
        self._session.commit()
        return len(rows)

    def _to_row(self, result: ResultMetadata) -> RunResult:
        created_at = _format_timestamp(result.created_at)
        updated_at = _format_timestamp(result.updated_at)
        return RunResult(
            run_id=result.run_id,
            query_id=result.query_id,
            query_text=result.query_text,
            search_query=result.search_query,
            domain=result.domain,
            title=result.title,
            snippet=result.snippet,
            raw_url=result.raw_url,
            final_url=result.final_url,
            created_at=created_at,
            updated_at=updated_at,
            raw_html_path=result.raw_html_path,
            visible_text=result.visible_text,
            fetch_error=result.fetch_error,
            extract_error=result.extract_error,
        )


def _format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")
