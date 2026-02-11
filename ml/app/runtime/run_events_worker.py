from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Mapping

import redis
from redis.exceptions import RedisError

from app.pipelines.ingestion import RunInput, ingest_run
from app.schemas.events import build_run_event
from app.services.fetcher import DeterministicMockUrlResolver, FetcherError, UrlResolver
from app.services.google_search import (
    DeterministicMockSearchClient,
    GoogleSearchClient,
    GoogleSearchConfig,
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

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        last_id = "$"
        while not self._stop_event.is_set():
            try:
                streams = self._redis.xread({self._stream_key: last_id}, count=10, block=1000)
            except RedisError as error:
                self._logger.warning("run_worker.redis_read_failed error=%s", error)
                time.sleep(1)
                continue

            if not streams:
                continue

            for _, messages in streams:
                for message_id, fields in messages:
                    last_id = message_id
                    self._process_event(fields)

    def _process_event(self, fields: Mapping[str, str]) -> None:
        event = _parse_run_requested_event(fields, logger=self._logger)
        if event is None:
            return

        try:
            run_inputs = _extract_run_inputs(event.payload)
            search_client, url_resolver = _build_clients(self._search_provider, self._logger)
            outcome = ingest_run(
                run_id=event.run_id,
                run_inputs=run_inputs,
                search_client=search_client,
                url_resolver=url_resolver,
                data_dir=self._data_dir,
                capture_html=True,
            )
            self._publish_event(
                COMPLETED_EVENT_TYPE,
                event.run_id,
                {
                    "status": "completed",
                    "issuedCalls": outcome.issued_calls,
                    "persistedResults": outcome.persisted_results,
                    "skipped404": outcome.skipped_404,
                },
            )
        except (SearchServiceError, FetcherError, TimeoutError) as error:
            self._publish_event(
                FAILED_EVENT_TYPE,
                event.run_id,
                {
                    "errorCode": "NETWORK_ERROR",
                    "message": str(error),
                },
            )
        except Exception as error:
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


def _build_clients(provider: str, logger: logging.Logger):
    if provider == "mock":
        return DeterministicMockSearchClient(logger=logger), DeterministicMockUrlResolver()

    if provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "").strip()
        if not api_key or not search_engine_id:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID are required for google provider")
        client = GoogleSearchClient(
            GoogleSearchConfig(api_key=api_key, search_engine_id=search_engine_id),
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
        logger.warning("run_worker.invalid_event missing_fields=%s", ",".join(missing))
        return None

    if fields["eventType"] != REQUESTED_EVENT_TYPE:
        return None

    try:
        int(fields["eventVersion"])
        datetime.fromisoformat(fields["occurredAt"].replace("Z", "+00:00"))
    except ValueError:
        logger.warning("run_worker.invalid_event invalid_metadata eventId=%s", fields.get("eventId"))
        return None

    try:
        payload = json.loads(fields["payload"])
    except json.JSONDecodeError:
        logger.warning("run_worker.invalid_event invalid_payload eventId=%s", fields.get("eventId"))
        return None

    if not isinstance(payload, dict):
        logger.warning("run_worker.invalid_event payload_not_object eventId=%s", fields.get("eventId"))
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
