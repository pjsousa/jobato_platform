# ML Module

A job relevance scoring and model management system built with FastAPI.

## Core Components

### Pipelines (`app/pipelines/`)

| Pipeline | Purpose |
|----------|---------|
| `ingestion.py` | Orchestrates job data collection: Brave Search → URL resolution → HTML fetching → text extraction → storage |
| `dedupe.py` | Two-phase deduplication: exact URL matching + text similarity (Jaccard on n-grams) |
| `scoring.py` | Assigns relevance scores (-1 to 1) using active ML model; duplicates inherit canonical scores |
| `evaluation.py` | Runs parallel model evaluations against labeled datasets; computes metrics |
| `retrain.py` | Retrains active model on newly labeled data; pickles artifacts |
| `run_pipeline.py` | Quota-aware execution wrapper with concurrency limits |

### Services (`app/services/`)

| Service | Purpose |
|---------|---------|
| `model_activation.py` | Promotes models to "active", handles rollback |
| `model_selector.py` | Compares model performance for selection |
| `evaluation_store.py` | SQLite persistence for evaluations, activations, retrain jobs |
| `retrain_scheduler.py` | Cron-style daily retrain scheduling |
| `brave_search.py` | External Brave Search API client with configurable freshness filtering |
| `fetcher.py` / `html_fetcher.py` | URL resolution and HTML fetching |
| `html_extractor.py` | Visible text extraction from HTML |
| `url_normalizer.py` | URL canonicalization for deduplication |
| `cache.py` | Search result caching service |
| `quota.py` | API quota management |

### Registry (`app/registry/`)

- `model_interface.py`: Abstract contract (`fit`/`predict`) for pluggable ML models
- `model_registry.py`: YAML-driven model discovery and loading
- `config_loader.py`: Configuration loading from YAML files

### Database (`app/db/`)

- SQLAlchemy models (`RunResult`) storing job postings with scoring/dedupe fields
- Alembic migrations for schema evolution

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with Redis and model status |
| `/ml/models` | GET | List registered models |
| `/ml/models/active` | GET | Get currently active model |
| `/ml/models/history` | GET | Get model activation history |
| `/ml/models/comparisons` | GET | Model performance comparison |
| `/ml/models/{id}/activate` | POST | Activate a model |
| `/ml/models/{id}/rollback` | POST | Rollback to previous model version |
| `/ml/evaluations` | POST | Trigger model evaluation |
| `/ml/evaluations/{id}` | GET | Get evaluation status |
| `/ml/evaluations/{id}/results` | GET | Get evaluation results |
| `/ml/retrain/trigger` | POST | Manual retrain trigger |
| `/ml/retrain/status` | GET | Current retrain status |
| `/ml/retrain/history` | GET | Retrain job history |

## Data Flow

```
Query configs → Brave Search → HTML Fetch → Text Extract 
     → Dedupe → Score with Active Model → Store in SQLite
```

## Pipeline Triggering

The ingestion pipeline is triggered via **Redis Streams**. On startup, the `RunEventsWorker` listens to the `ml:run-events` stream.

### Triggering a Run

Publish a `run.requested` event to the stream:

```python
import redis
import json
from uuid import uuid4
from datetime import datetime, timezone

client = redis.Redis(host="localhost", port=6379, decode_responses=True)

client.xadd("ml:run-events", {
    "eventId": str(uuid4()),
    "eventType": "run.requested",
    "eventVersion": "1",
    "occurredAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "runId": str(uuid4()),
    "payload": json.dumps({
        "runInputs": [
            {
                "queryText": "python developer",
                "domain": "example.com",
                "searchQuery": "site:example.com python developer",
                "queryId": "q-123"
            }
        ]
    })
})
```

### Event Flow

1. `RunEventsWorker` reads event from `ml:run-events` stream (blocking `XREAD`, 1s timeout)
2. Parses `runInputs` from payload
3. Prepares SQLite database (copies existing `current-db.txt` or creates new)
4. Calls `ingest_run()` → search → fetch → extract → dedupe → score
5. Updates `current-db.txt` pointer to new database
6. Publishes `run.completed` or `run.failed` event back to stream

### Event Types

| Event Type | Direction | Description |
|------------|-----------|-------------|
| `run.requested` | Inbound | Triggers a new ingestion run |
| `run.completed` | Outbound | Run finished successfully |
| `run.failed` | Outbound | Run failed with error |

### Required Event Fields

All events must include: `eventId`, `eventType`, `eventVersion`, `occurredAt`, `runId`, `payload`

## Model Interface

Models must implement the `ModelInterface` abstract class:

```python
class ModelInterface(abc.ABC):
    @abc.abstractmethod
    def fit(self, X, y) -> "ModelInterface":
        """Train the model on the provided data."""
        
    @abc.abstractmethod
    def predict(self, X):
        """Predict relevance scores (-1 to 1)."""
```

## Configuration

- `config/ml/models.yaml` — Model registry configuration
- `config/ml/ml-config.yaml` — ML module settings (eval workers, etc.)
- `config/queries.yaml` — Search query definitions
- `config/allowlists.yaml` — Domain allowlists

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | localhost | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `CONFIG_DIR` | config | Configuration directory path |
| `DATA_DIR` | data | Data storage directory |
| `RETRAIN_ENABLED` | true | Enable scheduled retraining |
| `RETRAIN_SCHEDULE` | 0 6 * * * | Cron schedule for retraining |
| `JOBATO_SEARCH_PROVIDER` | mock | Search provider: `mock` (deterministic mock) or `brave` (live search) |
| `BRAVE_SEARCH_API_KEY` | *(required)* | Brave Search API subscription token (required when provider=brave) |
| `BRAVE_SEARCH_FRESHNESS` | pm | Freshness filter for search results |

### Search Freshness Options

The `BRAVE_SEARCH_FRESHNESS` environment variable controls how recent the search results should be:

| Value | Meaning |
|-------|---------|
| `pd` | Past 24 hours |
| `pw` | Past 7 days |
| `pm` | Past 31 days (default) |
| `py` | Past year |
| `2024-01-01to2024-06-30` | Custom date range (format: `YYYY-MM-DDtoYYYY-MM-DD`) |

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload
```

## Testing

```bash
pytest ml/tests/
```
