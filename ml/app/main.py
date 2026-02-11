import os

import redis
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.runtime import RunEventsWorker

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
_run_events_worker: RunEventsWorker | None = None


def _redis_reachable() -> bool:
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        socket_connect_timeout=1,
        socket_timeout=1,
    )
    client.ping()
    return True


@app.get("/health")
def health() -> dict:
    try:
        _redis_reachable()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "redis": "unreachable"},
        )

    return {"status": "ok", "redis": "ok"}


@app.on_event("startup")
def startup() -> None:
    global _run_events_worker
    _run_events_worker = RunEventsWorker()
    _run_events_worker.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if _run_events_worker is not None:
        _run_events_worker.stop()
