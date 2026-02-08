# Test Design: Epic 1 - Configure Search Scope

**Date:** 2026-02-08
**Author:** Pedro
**Status:** Draft

---

## Executive Summary

**Scope:** full test design for Epic 1

**Risk Summary:**

- Total risks identified: 5
- High-priority risks (score >= 6): 2
- Critical categories: DATA, TECH

**Coverage Summary:**

- P0 scenarios: 4
- P1 scenarios: 10
- P2/P3 scenarios: 4

---

## Context and Existing Coverage

### Documents Used

- PRD: `_bmad-output/planning-artifacts/prd.md`
- Epic: `_bmad-output/planning-artifacts/epics.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`

### Existing Tests (Epic 1 Related)

- Frontend:
  - `frontend/src/features/queries/components/QueryManager.test.tsx`
  - `frontend/src/features/allowlist/components/AllowlistForm.test.tsx`
  - `frontend/src/features/allowlist/components/AllowlistTable.test.tsx`
- API:
  - `api/src/test/java/com/jobato/api/service/QueryServiceTest.java`
  - `api/src/test/java/com/jobato/api/controller/AllowlistControllerTest.java`
  - `api/src/test/java/com/jobato/api/service/RunInputServiceTest.java`
  - `api/src/test/java/com/jobato/api/service/RunInputNormalizerTest.java`
  - `api/src/test/java/com/jobato/api/service/AllowlistDomainNormalizerTest.java`
  - `api/src/test/java/com/jobato/api/repository/AllowlistRepositoryTest.java`
- ML: No tests found under `ml/tests/`

### Coverage Gaps

- API controller tests for query endpoints (create, update, list, duplicate validation)
- UI validation states for duplicate queries and invalid domains
- End-to-end flow for query + allowlist config to run-input generation (API boundary)

---

## Risk Assessment

### High-Priority Risks (Score >= 6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-001 | DATA | Run inputs omit or duplicate query x domain combinations after normalization and dedupe | 2 | 3 | 6 | Expand service tests for ordering, dedupe, and empty-input behavior; add controller tests for run-input generation entry point | DEV |
| R-002 | TECH | Duplicate queries or domains slip through API normalization rules, creating inconsistent run inputs | 2 | 3 | 6 | Add controller tests for duplicates and update flows; align validation error messages across API and UI | DEV |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-003 | DATA | Disabled queries or domains still appear in run inputs | 2 | 2 | 4 | Keep RunInputService filtering tests and add API-level coverage for disabled entries | DEV |
| R-004 | BUS | UI edit flows fail to persist updates for queries or allowlists | 2 | 2 | 4 | Add component tests for edit and save flows and API mutation failures | DEV |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R-005 | OPS | Missing config files result in empty lists without clear UI guidance | 1 | 2 | 2 | Monitor and add empty-state messaging tests | DEV |

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## Test Coverage Plan

### P0 (Critical)

**Criteria:** Blocks core journey, high risk (score >= 6), no workaround

| Requirement | Test Level | Risk Link | Planned Scenarios | Owner | Notes |
| ----------- | ---------- | --------- | ----------------- | ----- | ----- |
| Story 1.4: Generate query x domain combinations | Service | R-001 | 1.4-SVC-001, 1.4-SVC-002 | DEV | Covers ordering, enabled filtering, and search query format |
| Story 1.2/1.3: Reject duplicates after normalization | API | R-002 | 1.2-API-004, 1.3-API-004 | DEV | Ensure consistent validation errors |

### P1 (High)

**Criteria:** Important features, medium risk (score 3-4), common workflows

| Requirement | Test Level | Risk Link | Planned Scenarios | Owner | Notes |
| ----------- | ---------- | --------- | ----------------- | ----- | ----- |
| Story 1.2: Create query defaults | API | R-003 | 1.2-API-001 | DEV | Verify enabled defaults and normalization |
| Story 1.2: Edit and disable query | API | R-003 | 1.2-API-002, 1.2-API-003 | DEV | Preserve createdAt, update updatedAt |
| Story 1.3: Create allowlist defaults | API | R-003 | 1.3-API-001 | DEV | Enabled by default |
| Story 1.3: Edit and disable allowlist | API | R-003 | 1.3-API-002, 1.3-API-003 | DEV | Persist updated domain |
| Story 1.3: Reject invalid domains | API | R-003 | 1.3-API-004 | DEV | Validate format rules |
| Story 1.2 UI: Add/edit/disable query | Component | R-004 | 1.2-UI-001, 1.2-UI-002, 1.2-UI-003 | DEV | Cover optimistic update hooks |
| Story 1.3 UI: Add/edit/toggle allowlist | Component | R-004 | 1.3-UI-001, 1.3-UI-002, 1.3-UI-003 | DEV | Cover callbacks and toggles |
| Story 1.4: Error when no enabled inputs | Service | R-003 | 1.4-SVC-003 | DEV | Ensure error messaging for empty inputs |

### P2 (Medium)

**Criteria:** Secondary features, low risk, edge cases

| Requirement | Test Level | Planned Scenarios | Owner | Notes |
| ----------- | ---------- | ----------------- | ----- | ----- |
| Story 1.1: Service health endpoints reachable | API | 1.1-API-001 | DEV | Smoke coverage for baseline setup |
| Story 1.3 UI: Invalid domain error states | Component | 1.3-UI-004 | DEV | Ensure error messaging is visible |
| Story 1.4: Normalization dedupe stability | Service | 1.4-SVC-004 | DEV | Stable ordering after dedupe |
| Story 1.1: Build and startup checks | Manual | 1.1-MAN-001 | DEV | Manual verification of docker-compose flow |

### P3 (Low)

No additional P3 scenarios identified for this epic.

---

## Execution Order

### Smoke Tests

**Purpose:** Fast feedback on core wiring

- [ ] 1.1-API-001 Service health endpoints

### P0 Tests

**Purpose:** Critical data correctness

- [ ] 1.4-SVC-001 Run input generation
- [ ] 1.4-SVC-002 Enabled filtering
- [ ] 1.2-API-004 Query duplicate rejection
- [ ] 1.3-API-004 Allowlist duplicate rejection

### P1 Tests

**Purpose:** Core user flows

- [ ] 1.2-API-001 Query create defaults
- [ ] 1.2-API-002 Query edit
- [ ] 1.2-API-003 Query disable
- [ ] 1.3-API-001 Allowlist create defaults
- [ ] 1.3-API-002 Allowlist edit
- [ ] 1.3-API-003 Allowlist disable
- [ ] 1.2-UI-001 Query add
- [ ] 1.2-UI-002 Query edit
- [ ] 1.2-UI-003 Query toggle
- [ ] 1.3-UI-001 Allowlist add
- [ ] 1.3-UI-002 Allowlist edit
- [ ] 1.3-UI-003 Allowlist toggle
- [ ] 1.4-SVC-003 Empty inputs error

### P2/P3 Tests

**Purpose:** Edge cases and manual checks

- [ ] 1.3-UI-004 Invalid domain UI error
- [ ] 1.4-SVC-004 Normalization stability
- [ ] 1.1-MAN-001 Baseline startup verification

---

## Resource Considerations

### Test Data

- Use `@TempDir` for file-backed repositories in API tests
- Use in-memory test fixtures for UI components

### Tooling

- Frontend: Vitest + Testing Library
- API: Spring Boot Test + MockMvc + JUnit

### Environment

- API tests use file-backed config paths under a temp directory
- Frontend tests use jsdom with mocked hooks

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: >=95% (waivers required for failures)
- **P2/P3 pass rate**: >=90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: >=80%
- **Security scenarios**: 100%
- **Business logic**: >=70%
- **Edge cases**: >=50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (score >= 6) items unmitigated
- [ ] Security tests (SEC category) pass 100%

---

## Mitigation Plans

### R-001: Run input combinations are incorrect (Score: 6)

**Mitigation Strategy:** Expand RunInputService and RunInputNormalizer tests to cover ordering, dedupe, and disabled filters. Add API boundary tests if run input generation is exposed.
**Owner:** DEV
**Status:** Planned
**Verification:** Green service and controller tests; stable run input ordering

### R-002: Duplicate inputs accepted through normalization gaps (Score: 6)

**Mitigation Strategy:** Add API controller tests for duplicate query and allowlist creation, and align normalization rules for create and update flows.
**Owner:** DEV
**Status:** Planned
**Verification:** Duplicate submissions return validation errors; no duplicate records in config store

---

## Assumptions and Dependencies

### Assumptions

1. Query and allowlist configuration is persisted in file-backed config under `config/`.
2. The API exposes query and allowlist endpoints per architecture.
3. UI uses TanStack Query hooks for data operations.

### Dependencies

1. Query and allowlist API endpoints implemented and stable.
2. Run input generation service accessible from API run workflow.

### Risks to Plan

- **Risk:** UI shows stale data after updates
  - **Impact:** Confusing UX, incorrect enablement state
  - **Contingency:** Add query cache invalidation tests in hooks

---

## Follow-on Workflows (Manual)

- Run `*atdd` to generate failing P0 tests (separate workflow; not auto-run).
- Run `*automate` for broader coverage once implementation exists.

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: TBD
- [ ] Tech Lead: TBD
- [ ] QA Lead: TBD

**Comments:**

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization

### Related Documents

- PRD: `_bmad-output/planning-artifacts/prd.md`
- Epic: `_bmad-output/planning-artifacts/epics.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `_bmad/bmm/testarch/test-design`
**Version**: 4.0 (BMad v6)
