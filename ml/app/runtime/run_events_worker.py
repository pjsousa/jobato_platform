from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
import threading
import time
from typing import Any, Mapping

import redis
from redis.exceptions import RedisError

from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.events import build_run_event
from app.services.fetcher import DeterministicMockUrlResolver, FetcherError, UrlResolver
from app.services.brave_search import (
    BraveSearchClient,
    BraveSearchConfig,
    DeterministicMockSearchClient,
    SearchServiceError,
)


STREAM_KEY = "ml:run-events"
REQUESTED_EVENT_TYPE = "run.requested"
COMPLETED_EVENT_TYPE = "run.completed"
FAILED_EVENT_TYPE = "run.failed"
REQUIRED_EVENT_FIELDS = (
    "eventId",
    "eventType",
    "eventVersion",
    "occurredAt",
    "runId",
    "payload",
)
DEFAULT_ACTIVE_DB = "db/runs/active.db"


def _resolve_active_db_path(data_dir: Path) -> Path | None:
    pointer_path = data_dir / "db" / "current-db.txt"
    if pointer_path.exists():
        pointer_value = pointer_path.read_text(encoding="utf-8").strip()
        if pointer_value:
            resolved = Path(pointer_value)
            db_path = resolved if resolved.is_absolute() else data_dir / resolved
            if db_path.exists():
                return db_path
    default_path = data_dir / DEFAULT_ACTIVE_DB
    if default_path.exists():
        return default_path
    return None


def _prepare_run_database(run_id: str, data_dir: Path, logger: logging.Logger) -> Path:
    runs_dir = data_dir / "db" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    new_db_path = runs_dir / f"{run_id}.db"

    source_db = _resolve_active_db_path(data_dir)
    if source_db is not None:
        source_size = source_db.stat().st_size if source_db.exists() else 0
        logger.info(
            "run_worker.db_prepared run_id=%s source=%s source_size=%db target=%s",
            run_id, source_db.name, source_size, new_db_path.name
        )
        shutil.copy2(source_db, new_db_path)
    else:
        logger.info("run_worker.db_created run_id=%s target=%s", run_id, new_db_path.name)
        new_db_path.parent.mkdir(parents=True, exist_ok=True)
        new_db_path.touch()

    return new_db_path


def _update_db_pointer(new_db_path: Path, data_dir: Path, logger: logging.Logger) -> None:
    pointer_path = data_dir / "db" / "current-db.txt"
    relative_path = new_db_path.relative_to(data_dir)
    pointer_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = pointer_path.with_suffix(".tmp")
    temp_path.write_text(str(relative_path), encoding="utf-8")
    temp_path.replace(pointer_path)
    
    db_size = new_db_path.stat().st_size if new_db_path.exists() else 0
    logger.info(
        "run_worker.db_pointer_updated path=%s db_size=%db",
        str(relative_path), db_size
    )


@dataclass(frozen=True)
class RequestedRunEvent:
    run_id: str
    payload: dict[str, Any]


class RunEventsWorker:
    def __init__(
        self,
        *,
        redis_client: redis.Redis | None = None,
        logger: logging.Logger | None = None,
        stream_key: str = STREAM_KEY,
        search_provider: str | None = None,
        data_dir: Path | str | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._stream_key = stream_key
        self._search_provider = (search_provider or os.getenv("JOBATO_SEARCH_PROVIDER", "mock")).strip().lower()
        if not self._search_provider:
            self._search_provider = "mock"

        self._data_dir = Path(data_dir or os.getenv("DATA_DIR", "data"))
        self._redis = redis_client or redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="run-events-worker", daemon=True)
        self._thread.start()
        self._logger.info(
            "run_worker.started provider=%s stream=%s data_dir=%s",
            self._search_provider, self._stream_key, self._data_dir
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._logger.info("run_worker.stopped")

    def _run(self) -> None:
        last_id = "$"
        while not self._stop_event.is_set():
            try:
                streams = self._redis.xread({self._stream_key: last_id}, count=10, block=1000)
            except RedisError as error:
                self._logger.warning("run_worker.redis_error error=%s", error)
                time.sleep(1)
                continue

            if not streams:
                continue

            for _, messages in streams:
                for message_id, fields in messages:
                    last_id = message_id
                    payload_raw = fields.get("payload", "")
                    payload_size = len(payload_raw) if payload_raw else 0
                    self._logger.info(
                        "run_worker.event_received event_id=%s run_id=%s event_type=%s payload_size=%db",
                        fields.get("eventId", "unknown")[:8],
                        fields.get("runId", "unknown")[:8],
                        fields.get("eventType", "unknown"),
                        payload_size
                    )
                    self._process_event(fields)

    def _process_event(self, fields: Mapping[str, str]) -> None:
        event = _parse_run_requested_event(fields, logger=self._logger)
        if event is None:
            return

        start_time = time.perf_counter()
        run_inputs = _extract_run_inputs(event.payload)
        self._logger.info(
            "run_worker.processing_start run_id=%s inputs=%d",
            event.run_id[:8], len(run_inputs)
        )

        try:
            search_client, url_resolver = _build_clients(self._search_provider, self._logger)
            _prepare_run_database(event.run_id, self._data_dir, self._logger)
            outcome = ingest_run(
                run_id=event.run_id,
                run_inputs=run_inputs,
                search_client=search_client,
                url_resolver=url_resolver,
                data_dir=self._data_dir,
                capture_html=True,
            )
            new_db_path = self._data_dir / "db" / "runs" / f"{event.run_id}.db"
            _update_db_pointer(new_db_path, self._data_dir, self._logger)
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._logger.info(
                "run_worker.processing_complete run_id=%s issued=%d persisted=%d new=%d skipped_404=%d zero_results=%d duration_ms=%d",
                event.run_id[:8],
                outcome.issued_calls,
                outcome.persisted_results,
                outcome.new_jobs_count,
                outcome.skipped_404,
                len(outcome.zero_results),
                duration_ms
            )
            
            self._publish_event(
                COMPLETED_EVENT_TYPE,
                event.run_id,
                {
                    "status": "completed",
                    "issuedCalls": outcome.issued_calls,
                    "persistedResults": outcome.persisted_results,
                    "newJobsCount": outcome.new_jobs_count,
                    "relevantCount": 0,
                    "skipped404": outcome.skipped_404,
                    "zeroResults": [
                        {
                            "queryText": item.query_text,
                            "domain": item.domain,
                            "occurredAt": item.occurred_at,
                        }
                        for item in outcome.zero_results
                    ],
                },
            )
        except (SearchServiceError, FetcherError, TimeoutError) as error:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._logger.warning(
                "run_worker.processing_failed run_id=%s error_code=NETWORK_ERROR error=%s duration_ms=%d",
                event.run_id[:8], str(error)[:100], duration_ms
            )
            self._publish_event(
                FAILED_EVENT_TYPE,
                event.run_id,
                {
                    "errorCode": "NETWORK_ERROR",
                    "message": str(error),
                },
            )
        except Exception as error:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self._logger.warning(
                "run_worker.processing_failed run_id=%s error_code=INGESTION_ERROR error=%s duration_ms=%d",
                event.run_id[:8], str(error)[:100], duration_ms
            )
            self._publish_event(
                FAILED_EVENT_TYPE,
                event.run_id,
                {
                    "errorCode": "INGESTION_ERROR",
                    "message": str(error),
                },
            )

    def _publish_event(self, event_type: str, run_id: str, payload: dict[str, Any]) -> None:
        event = build_run_event(event_type=event_type, run_id=run_id, payload=payload)
        fields = {
            "eventId": str(event["eventId"]),
            "eventType": str(event["eventType"]),
            "eventVersion": str(event["eventVersion"]),
            "occurredAt": str(event["occurredAt"]),
            "runId": str(event["runId"]),
            "payload": json.dumps(event["payload"]),
        }
        self._redis.xadd(self._stream_key, fields)
        payload_size = len(fields["payload"])
        self._logger.info(
            "run_worker.event_published run_id=%s event_type=%s payload_size=%db",
            run_id[:8], event_type, payload_size
        )


def _build_clients(provider: str, logger: logging.Logger):
    if provider == "mock":
        return DeterministicMockSearchClient(logger=logger), DeterministicMockUrlResolver()

    if provider == "brave":
        api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        if not api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY is required for brave provider")
        freshness = os.getenv("BRAVE_SEARCH_FRESHNESS", "pm").strip()
        client = BraveSearchClient(
            BraveSearchConfig(api_key=api_key, freshness=freshness),
            logger=logger,
        )
        return client, UrlResolver()

    raise ValueError(f"Unsupported search provider: {provider}")


def _parse_run_requested_event(
    fields: Mapping[str, str],
    *,
    logger: logging.Logger,
) -> RequestedRunEvent | None:
    missing = [field for field in REQUIRED_EVENT_FIELDS if not fields.get(field)]
    if missing:
        logger.warning(
            "run_worker.event_invalid reason=missing_fields fields=%s",
            ",".join(missing)
        )
        return None

    event_id = fields.get("eventId", "unknown")[:8]
    if fields["eventType"] != REQUESTED_EVENT_TYPE:
        logger.debug(
            "run_worker.event_skipped event_id=%s event_type=%s",
            event_id, fields["eventType"]
        )
        return None

    try:
        int(fields["eventVersion"])
        datetime.fromisoformat(fields["occurredAt"].replace("Z", "+00:00"))
    except ValueError:
        logger.warning(
            "run_worker.event_invalid event_id=%s reason=invalid_metadata",
            event_id
        )
        return None

    try:
        payload = json.loads(fields["payload"])
    except json.JSONDecodeError:
        logger.warning(
            "run_worker.event_invalid event_id=%s reason=invalid_json_payload",
            event_id
        )
        return None

    if not isinstance(payload, dict):
        logger.warning(
            "run_worker.event_invalid event_id=%s reason=payload_not_object",
            event_id
        )
        return None

    return RequestedRunEvent(run_id=fields["runId"], payload=payload)


def _extract_run_inputs(payload: Mapping[str, Any]) -> list[RunInput]:
    raw_inputs = payload.get("runInputs")
    if not isinstance(raw_inputs, list):
        raise ValueError("payload.runInputs must be a list")

    run_inputs: list[RunInput] = []
    for item in raw_inputs:
        if not isinstance(item, dict):
            raise ValueError("payload.runInputs must contain objects")

        query_text = str(item.get("queryText", "")).strip()
        domain = str(item.get("domain", "")).strip()
        search_query = str(item.get("searchQuery", "")).strip()
        query_id_value = item.get("queryId")
        query_id = str(query_id_value).strip() if query_id_value is not None else None
        if query_id == "":
            query_id = None

        if not query_text or not domain or not search_query:
            raise ValueError("Each runInput must include queryText, domain, and searchQuery")

        run_inputs.append(
            RunInput(
                query_id=query_id,
                query_text=query_text,
                domain=domain,
                search_query=search_query,
            )
        )

    return run_inputs
