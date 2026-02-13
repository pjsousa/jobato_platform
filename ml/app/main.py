import os
import logging
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app.runtime import RunEventsWorker
from app.registry import initialize_registry, get_registry
from app.pipelines.evaluation import EvaluationPipeline, get_results, get_status
from app.services.evaluation_store import EvaluationStore
from app.services.model_activation import ModelActivationError, ModelActivationService
from app.services.model_selector import ModelSelector

app = FastAPI()
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
_run_events_worker: RunEventsWorker | None = None
_evaluation_store: EvaluationStore | None = None
_evaluation_pipeline: EvaluationPipeline | None = None
_model_activation_service: ModelActivationService | None = None
_model_selector: ModelSelector | None = None


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


def _evaluation_db_path() -> Path:
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    return data_dir / "db" / "evaluations.db"


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


@app.post("/ml/evaluations", status_code=status.HTTP_202_ACCEPTED)
async def trigger_evaluation() -> dict:
    if _evaluation_pipeline is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Evaluation service unavailable")
    return _evaluation_pipeline.trigger_evaluation()


@app.get("/ml/models/comparisons")
def get_model_comparisons() -> dict:
    if _model_selector is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model selector unavailable")
    return _model_selector.comparisons_payload()


@app.post("/ml/models/{model_id}/activate")
def activate_model(model_id: str) -> dict:
    if _model_activation_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model activation unavailable")
    try:
        activated = _model_activation_service.activate_model(model_id=model_id)
    except ModelActivationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "modelId": activated.model_id,
        "modelVersion": activated.model_version,
        "activatedAt": activated.activated_at,
        "activatedBy": activated.activated_by,
        "evaluationId": activated.evaluation_id,
    }


@app.post("/ml/models/{model_id}/rollback")
def rollback_model(model_id: str) -> dict:
    if _model_activation_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model activation unavailable")
    try:
        activated = _model_activation_service.rollback_model(model_id=model_id)
    except ModelActivationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "modelId": activated.model_id,
        "modelVersion": activated.model_version,
        "activatedAt": activated.activated_at,
        "activatedBy": activated.activated_by,
        "evaluationId": activated.evaluation_id,
        "action": "rollback",
    }


@app.get("/ml/models/active")
def get_active_model() -> dict:
    if _model_activation_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model activation unavailable")
    return _model_activation_service.active_model_payload()


@app.get("/ml/models/history")
def get_model_history() -> dict:
    if _model_activation_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model activation unavailable")
    return _model_activation_service.history_payload()


@app.get("/ml/evaluations/{evaluation_id}")
def evaluation_status(evaluation_id: str) -> dict:
    if _evaluation_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Evaluation service unavailable")
    payload = get_status(_evaluation_store, evaluation_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return payload


@app.get("/ml/evaluations/{evaluation_id}/results")
def evaluation_results(evaluation_id: str) -> dict:
    if _evaluation_store is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Evaluation service unavailable")
    payload = get_status(_evaluation_store, evaluation_id)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return get_results(_evaluation_store, evaluation_id)


@app.on_event("startup")
def startup() -> None:
    global _run_events_worker, _evaluation_store, _evaluation_pipeline, _model_activation_service, _model_selector

    config_path = _registry_config_path()
    registry = initialize_registry(config_path)
    logger.info(
        "startup.registry initialized=%s models=%s errors=%d",
        registry.is_initialized,
        [model["identifier"] for model in registry.get_available_models()],
        len(registry.load_errors),
    )

    _evaluation_store = EvaluationStore(_evaluation_db_path())
    _evaluation_pipeline = EvaluationPipeline(store=_evaluation_store, registry=registry)
    _model_activation_service = ModelActivationService(store=_evaluation_store, registry=registry)
    _model_selector = ModelSelector(_evaluation_store)

    _run_events_worker = RunEventsWorker()
    _run_events_worker.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if _run_events_worker is not None:
        _run_events_worker.stop()
