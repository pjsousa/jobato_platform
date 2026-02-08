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

## Epic 2: Run & Capture Results Validation

### What's Available After Epic 2 Completion

After completing Epic 2, you should be able to test the following core functionalities:
1. **Manual Run Triggering** - Start a run manually through the UI
2. **Run Orchestration** - System manages concurrent execution and prevents overlapping runs
3. **Quota Management** - System enforces daily quota limits and handles quota exhaustion
4. **Result Capture** - Fetches Google Search results, follows redirects, ignores 404s, and stores metadata
5. **Caching and Revisit Management** - Implements 12-hour TTL caching and 1-week revisit throttling
6. **Run Reporting** - Displays run status, metrics, and zero-result logging
7. **Integration Testing** - Redis Streams communication between ML and API services

### Step-by-Step Validation Flow

#### Step 1: Verify System Status
Before starting any run test:
1. Confirm all services are running (`docker-compose ps`)
2. Check API health endpoint: `http://localhost:8080/api/health` 
3. Verify ML health endpoint: `http://localhost:8000/health`
4. Confirm Redis is accessible
5. Check that query and allowlist configurations exist in `config/` directory

#### Step 2: Configure Test Environment
1. Ensure you have at least one enabled query in the system
2. Set up at least one allowlist domain for testing
3. Verify quota settings in `config/quota.yaml` (for testing purposes, you might want to set a low limit)

#### Step 3: Trigger a Manual Run
1. Navigate to the run control interface in the UI
2. Click the "Run Now" or "Manual Trigger" button
3. Observe the system status changing to "running"

#### Step 4: Monitor Run Process
1. Check API logs to see the run.requested event published to Redis Streams
2. Monitor ML service logs for:
   - Google Search API calls
   - Result processing
   - Data storage in SQLite
   - Caching behavior (if results are reused from cache)
   - URL revisit throttling (if applicable)
3. Verify no concurrent runs occur when a run is already in progress

#### Step 5: Validate Quota Enforcement
1. When running with low quota limits:
   - Observe quota enforcement behavior
   - Test what happens when quota is reached (should block additional API calls)
   - Check that run status shows appropriate error message when blocked by quota

#### Step 6: Check Result Storage
1. Verify results are properly stored in the database
2. Confirm metadata (title, snippet, domain, timestamps) is saved
3. Verify raw HTML is stored in data/html directory
4. Check that visible text extraction was performed and stored

#### Step 7: Verify Run Reporting
1. Request the last run status from API
2. Verify run summary metrics are displayed:
   - Trigger time
   - Duration
   - New jobs count
   - Relevant count
3. Confirm run status shows success, partial, or failed appropriately

#### Step 8: Test Caching and Revisit Throttling
1. Run a set of queries twice
2. Verify that cached results are used on the second run (within TTL)
3. Check that URLs are not revisited within a week if cached

### Setup Requirements for Testing Epic 2

#### Prerequisites
- Docker and Docker Compose properly installed and configured
- Node.js and Java 17 available for service builds
- Python 3.8+ for ML service
- Make utility for build automation

#### Configuration Files Required
Ensure these files exist in your project:
1. `config/queries.yaml` - Test queries for execution
2. `config/allowlists.yaml` - Test domains to search
3. `config/quota.yaml` - Quota limits for testing
4. `frontend/.env` - Frontend configuration
5. `api/.env` - API service configuration  
6. `ml/.env` - ML service configuration

#### Service Dependencies
1. MongoDB or SQLite (as configured in architecture document)
2. Redis container for event streaming
3. Network connectivity between containers
4. Proper volume mounting for shared `config/` and `data/` directories

#### Testing Environment
- Access to Google Search API (with valid API key)
- Test account with appropriate quota limits
- Network connectivity to external domains

### Expected Outcomes After Successful Epic 2 Testing

Upon successful validation, these outcomes should be verified:
1. **Run Lifecycle Management**: Manual runs can be triggered, tracked, and properly completed
2. **Constraint Enforcing**: Quotas are respected and overlapping runs are prevented 
3. **Data Capture**: Results are retrieved, processed, and stored appropriately
4. **Caching Behavior**: Cache TTL settings work correctly for reusing results
5. **Revisit Throttling**: URL revisit restrictions prevent unnecessary API calls
6. **Reporting Accuracy**: Run summaries and status indicators are accurate
7. **Integration**: Redis streaming communication between services functions correctly
8. **API Responses**: All endpoints return correct data according to RFC 7807 error format

## Disclaimer

This guide reflects the state of the project at the end of Epic 1 as of February 8, 2026. Subsequent epics may change commands, endpoints, or verification steps.
