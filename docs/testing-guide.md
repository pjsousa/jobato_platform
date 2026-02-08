# Testing Guide

This guide explains where tests live, how to run them, and how to start testing Epic 1.

---

## Test Locations

- Frontend: co-located `*.test.ts(x)` under `frontend/src/`
- API: `api/src/test/java`
- ML: `ml/tests/` (no tests found yet)

---

## Running Tests

### Frontend (Vitest)

From `frontend/`:

```bash
npm test
```

Optional watch mode:

```bash
npm run test:watch
```

### API (Spring Boot + JUnit)

From `api/`:

```bash
./gradlew test
```

### ML (Pytest)

Tests should live under `ml/tests/`. If you add tests, add `pytest` to `ml/requirements.txt` (or a dev requirements file) and run:

```bash
pytest
```

---

## Epic 1: Where to Start Testing

Epic 1 covers query and allowlist configuration and run input generation. Start with the existing coverage, then fill the gaps:

1. Run existing tests to validate current behavior.
2. Add missing API controller tests for query endpoints.
3. Add UI validation tests for duplicate queries and invalid domains.
4. Add API boundary tests that confirm run input generation aligns with query + allowlist configuration.

### Existing Coverage (Epic 1)

Frontend:

- `frontend/src/features/queries/components/QueryManager.test.tsx`
- `frontend/src/features/allowlist/components/AllowlistForm.test.tsx`
- `frontend/src/features/allowlist/components/AllowlistTable.test.tsx`

API:

- `api/src/test/java/com/jobato/api/service/QueryServiceTest.java`
- `api/src/test/java/com/jobato/api/controller/AllowlistControllerTest.java`
- `api/src/test/java/com/jobato/api/service/RunInputServiceTest.java`
- `api/src/test/java/com/jobato/api/service/RunInputNormalizerTest.java`
- `api/src/test/java/com/jobato/api/service/AllowlistDomainNormalizerTest.java`
- `api/src/test/java/com/jobato/api/repository/AllowlistRepositoryTest.java`

### Recommended Next Tests

API controller tests (queries):

- Create query defaults to enabled and normalizes whitespace
- Reject duplicate query after normalization
- Edit query text and disable query
- List queries returns normalized, stable ordering

Frontend UI validation tests:

- Duplicate query submission shows validation error
- Invalid allowlist domain shows validation error

Run input boundary tests:

- Query + allowlist configuration generates correct search queries
- Disabled items are excluded from run inputs
- No enabled inputs returns a clear error

---

## Testing Notes by Layer

### Frontend

- Use Testing Library + Vitest (existing tests follow this pattern).
- Mock hooks to isolate component behavior.

### API

- Use Spring Boot Test + MockMvc for controller tests.
- Use `@TempDir` for file-backed config and repository isolation.
- Internal endpoints require the `X-Jobato-Api-Key` header.

### ML

- Keep tests in `ml/tests/` and focus on pipeline behavior and data integrity.

---

## Related Documents

- Epic test design: `_bmad-output/test-design-epic-1.md`
- PRD: `_bmad-output/planning-artifacts/prd.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`
