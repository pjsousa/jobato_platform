import os
import logging
from pathlib import Path

import redis
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.runtime import RunEventsWorker
from app.registry import initialize_registry, get_registry

app = FastAPI()
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
_run_events_worker: RunEventsWorker | None = None


def _registry_config_path() -> Path:
    config_dir = Path(os.getenv("CONFIG_DIR", "config"))
    return config_dir / "ml" / "models.yaml"


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
    registry = get_registry()
    model_ids = [model["identifier"] for model in registry.get_available_models()]

    try:
        _redis_reachable()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "redis": "unreachable", "models": model_ids},
        )

    return {"status": "ok", "redis": "ok", "models": model_ids}


@app.get("/ml/models")
def list_models() -> dict:
    registry = get_registry()
    return {
        "models": registry.get_available_models(),
        "errors": [
            {
                "identifier": error.identifier,
                "errorType": error.error_type,
                "error": error.error_message,
            }
            for error in registry.load_errors
        ],
    }


@app.on_event("startup")
def startup() -> None:
    global _run_events_worker

    config_path = _registry_config_path()
    registry = initialize_registry(config_path)
    logger.info(
        "startup.registry initialized=%s models=%s errors=%d",
        registry.is_initialized,
        [model["identifier"] for model in registry.get_available_models()],
        len(registry.load_errors),
    )

    _run_events_worker = RunEventsWorker()
    _run_events_worker.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if _run_events_worker is not None:
        _run_events_worker.stop()
