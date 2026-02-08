import os

import redis
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


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
