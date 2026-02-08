# Jobato Epic 1 Guide

This guide describes how to run Jobato and perform basic Epic 1 verification flows using Docker Compose and API calls.

## What Runs

The repository includes `docker-compose.yml`, which runs all core services for Epic 1:
- Frontend (Vite React)
- API (Spring Boot)
- ML (FastAPI)
- Redis

## Step-by-Step: Run Everything (Docker Compose)

1. Copy the root env file if you have not already:
```bash
cd /Users/pedro/Dev/jobato
cp .env.example .env
```

2. Start all services:
```bash
docker compose up --build
```

3. Verify endpoints:
- Frontend: http://localhost:5173
- API: http://localhost:8080/api
- ML: http://localhost:8000
- Redis: localhost:6379

4. Health checks:
```bash
curl http://localhost:8080/api/health
curl http://localhost:8000/health
```

If your environment enforces API keys, add:
```bash
-H "X-Jobato-Api-Key: <value>"
```

## Epic 1 Basic Verification Flows

### Story 1.1: Baseline Scaffold

- The health checks above should return HTTP 200.
- Optional container check:
```bash
docker compose ps
```

### Story 1.2: Manage Query Strings

1. List queries:
```bash
curl http://localhost:8080/api/queries
```

2. Create a query:
```bash
curl -X POST http://localhost:8080/api/queries \
  -H "Content-Type: application/json" \
  -d '{"text":"senior backend remote"}'
```

3. Edit a query (replace `<id>` with the returned id):
```bash
curl -X PATCH http://localhost:8080/api/queries/<id> \
  -H "Content-Type: application/json" \
  -d '{"text":"staff backend remote"}'
```

4. Disable a query:
```bash
curl -X PATCH http://localhost:8080/api/queries/<id> \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

5. Duplicate check (should return RFC 7807 error):
```bash
curl -X POST http://localhost:8080/api/queries \
  -H "Content-Type: application/json" \
  -d '{"text":"staff backend remote"}'
```

Persisted config is written to:
- `/Users/pedro/Dev/jobato/config/queries.yaml`

### Story 1.3: Manage Allowlist Domains

1. List allowlists:
```bash
curl http://localhost:8080/api/allowlists
```

2. Add a domain:
```bash
curl -X POST http://localhost:8080/api/allowlists \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com"}'
```

3. Disable a domain:
```bash
curl -X PATCH http://localhost:8080/api/allowlists/example.com \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

4. Invalid domain (should return RFC 7807 error):
```bash
curl -X POST http://localhost:8080/api/allowlists \
  -H "Content-Type: application/json" \
  -d '{"domain":"https://bad.example.com/path"}'
```

Persisted config is written to:
- `/Users/pedro/Dev/jobato/config/allowlists.yaml`

### Story 1.4: Generate Per-Site Query Combinations

Run the unit test for the run input builder:
```bash
cd /Users/pedro/Dev/jobato/api
./gradlew test --tests "com.jobato.api.service.RunInputServiceTest"
```

There is no public HTTP endpoint for combinations yet; that wiring is part of Epic 2 run initiation.

## Disclaimer

This guide reflects the state of the project at the end of Epic 1 as of February 8, 2026. Subsequent epics may change commands, endpoints, or verification steps.
