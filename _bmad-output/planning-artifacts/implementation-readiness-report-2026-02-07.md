# Implementation Readiness Assessment Report

**Date:** 2026-02-07
**Project:** jobato

## Document Inventory

### PRD
- /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/prd.md (8471 bytes, 2026-02-05 00:58:48)

### Architecture
- /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/architecture.md (33604 bytes, 2026-02-06 01:11:26)

### Epics & Stories
- /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/epics.md (25881 bytes, 2026-02-07 19:59:51)

### UX Design
- /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/ux-design-specification.md (15119 bytes, 2026-02-06 00:02:03)

### Duplicates
- None

### Missing Documents
- None

## Document Selection Confirmation

All listed documents are selected for assessment.

## PRD Analysis

### Functional Requirements

FR1: User can define and edit query strings.
FR2: User can enable or disable individual queries.
FR3: User can define and edit an allowlist of domains.
FR4: User can enable or disable individual allowlist domains.
FR5: System can generate per-site queries by combining query strings with allowlisted domains.
FR6: User can trigger a run manually.
FR7: System can limit concurrent query execution based on a global setting.
FR8: System can stop issuing new API calls when the daily quota limit is reached.
FR9: System can prevent overlapping runs when one is already in progress.
FR10: System can record run start and completion timestamps.
FR11: System can fetch Google Search results for each query x allowlist pair.
FR12: System can follow a single redirect for result URLs.
FR13: System can ignore results with 404 responses.
FR14: System can store job result metadata (title, snippet, domain, query string, timestamps).
FR15: System can store the raw HTML for visited job pages.
FR16: System can extract and store visible text from job pages.
FR17: System can avoid revisiting a job URL for at least one week.
FR18: System can cache search results with a 12-hour TTL.
FR19: System can normalize URLs to create a stable dedupe key.
FR20: System can detect duplicates using URL and text similarity.
FR21: System can link duplicates to a canonical record.
FR22: System can hide duplicate records by default while preserving them.
FR23: System can assign a relevance score from -1 to 1 for each job.
FR24: System can default new jobs to score 0 before model learning.
FR25: System can retrain the relevance model daily.
FR26: User can mark a job as irrelevant.
FR27: System can clear a manual label if the job reappears with new wording.
FR28: User can view "Today" results (new since last run).
FR29: User can view "All Time" results.
FR30: User can toggle visibility of irrelevant jobs.
FR31: System can sort results by first seen time.
FR32: System can display key fields (title, company, snippet, source, posted date).
FR33: System can show duplicate count for a canonical item.
FR34: System can show last run status (success/failed/partial).
FR35: System can display run summary metrics (trigger time, duration, new jobs count, relevant count).
FR36: System can surface an error when manual run is blocked by quota.
FR37: System can log when queries return zero results.

Total FRs: 37

### Non-Functional Requirements

NFR1: Today/All Time views load within 2 seconds for typical daily result sets.
NFR2: Scheduled or manual runs succeed at least 95% of the time.
NFR3: Failed runs are reported with a visible status indicator.
NFR4: Data is encrypted at rest and in transit.
NFR5: No authentication required in MVP (local use).
NFR6: Target WCAG AA compliance (baseline).

Total NFRs: 6

### Additional Requirements

- Success criteria include zero false positives/negatives for daily results and daily application targets.
- Technical success includes daily runs completing by 08:00 and manual runs staying within quota.
- MVP scope includes manual trigger scraper, relevance scoring with daily retrain, and a simple review UI.
- Web app constraints: SPA, modern browsers only, no SEO, no real-time features in MVP.
- Implementation focus: fast page load and low-friction review flows.
- MVP resources: solo developer (full-stack + data pipeline + basic ML).
- MVP must-have capabilities include manual trigger, data capture, relevance scoring, Today/All Time views, irrelevant toggle, and dedupe linkage.
- Risk mitigation: quota volatility (caching/deterministic ordering), relevance issues (feedback loop), resource constraints (strict MVP scope).

### PRD Completeness Assessment

- Requirements are explicit, numbered, and cover ingestion, dedupe, scoring, UI, and run reporting.
- Non-functional constraints are clear for performance, reliability, security, and accessibility.
- Business success criteria are not defined, and relevance accuracy targets are aspirational and may require refinement.
- Model definition details are intentionally open, which is acceptable but should be revisited during implementation readiness.

## Epic Coverage Validation

### Epic FR Coverage Extracted

FR1: Epic 1 (Story 1.2)
FR2: Epic 1 (Story 1.2)
FR3: Epic 1 (Story 1.3)
FR4: Epic 1 (Story 1.3)
FR5: Epic 1 (Story 1.4)
FR6: Epic 2 (Story 2.1)
FR7: Epic 2 (Story 2.2)
FR8: Epic 2 (Story 2.2)
FR9: Epic 2 (Story 2.1)
FR10: Epic 2 (Story 2.1)
FR11: Epic 2 (Story 2.3)
FR12: Epic 2 (Story 2.3)
FR13: Epic 2 (Story 2.3)
FR14: Epic 2 (Story 2.3)
FR15: Epic 2 (Story 2.4)
FR16: Epic 2 (Story 2.4)
FR17: Epic 2 (Story 2.5)
FR18: Epic 2 (Story 2.5)
FR19: Epic 3 (Story 3.1)
FR20: Epic 3 (Story 3.2)
FR21: Epic 3 (Story 3.2)
FR22: Epic 3 (Story 3.2)
FR23: Epic 3 (Story 3.3)
FR24: Epic 3 (Story 3.3)
FR25: Epic 3 (Story 3.7)
FR26: Epic 4 (Story 4.4)
FR27: Epic 4 (Story 4.4)
FR28: Epic 4 (Story 4.1)
FR29: Epic 4 (Story 4.1)
FR30: Epic 4 (Story 4.5)
FR31: Epic 4 (Story 4.6)
FR32: Epic 4 (Story 4.3)
FR33: Epic 4 (Story 4.3)
FR34: Epic 2 (Story 2.6)
FR35: Epic 2 (Story 2.6)
FR36: Epic 2 (Story 2.2)
FR37: Epic 2 (Story 2.6)

Total FRs in epics: 37

### Coverage Matrix

| FR Number | PRD Requirement | Epic Coverage | Status |
| --------- | --------------- | ------------- | ------ |
| FR1 | User can define and edit query strings. | Epic 1 Story 1.2 | ✓ Covered |
| FR2 | User can enable or disable individual queries. | Epic 1 Story 1.2 | ✓ Covered |
| FR3 | User can define and edit an allowlist of domains. | Epic 1 Story 1.3 | ✓ Covered |
| FR4 | User can enable or disable individual allowlist domains. | Epic 1 Story 1.3 | ✓ Covered |
| FR5 | System can generate per-site queries by combining query strings with allowlisted domains. | Epic 1 Story 1.4 | ✓ Covered |
| FR6 | User can trigger a run manually. | Epic 2 Story 2.1 | ✓ Covered |
| FR7 | System can limit concurrent query execution based on a global setting. | Epic 2 Story 2.2 | ✓ Covered |
| FR8 | System can stop issuing new API calls when the daily quota limit is reached. | Epic 2 Story 2.2 | ✓ Covered |
| FR9 | System can prevent overlapping runs when one is already in progress. | Epic 2 Story 2.1 | ✓ Covered |
| FR10 | System can record run start and completion timestamps. | Epic 2 Story 2.1 | ✓ Covered |
| FR11 | System can fetch Google Search results for each query x allowlist pair. | Epic 2 Story 2.3 | ✓ Covered |
| FR12 | System can follow a single redirect for result URLs. | Epic 2 Story 2.3 | ✓ Covered |
| FR13 | System can ignore results with 404 responses. | Epic 2 Story 2.3 | ✓ Covered |
| FR14 | System can store job result metadata (title, snippet, domain, query string, timestamps). | Epic 2 Story 2.3 | ✓ Covered |
| FR15 | System can store the raw HTML for visited job pages. | Epic 2 Story 2.4 | ✓ Covered |
| FR16 | System can extract and store visible text from job pages. | Epic 2 Story 2.4 | ✓ Covered |
| FR17 | System can avoid revisiting a job URL for at least one week. | Epic 2 Story 2.5 | ✓ Covered |
| FR18 | System can cache search results with a 12-hour TTL. | Epic 2 Story 2.5 | ✓ Covered |
| FR19 | System can normalize URLs to create a stable dedupe key. | Epic 3 Story 3.1 | ✓ Covered |
| FR20 | System can detect duplicates using URL and text similarity. | Epic 3 Story 3.2 | ✓ Covered |
| FR21 | System can link duplicates to a canonical record. | Epic 3 Story 3.2 | ✓ Covered |
| FR22 | System can hide duplicate records by default while preserving them. | Epic 3 Story 3.2 | ✓ Covered |
| FR23 | System can assign a relevance score from -1 to 1 for each job. | Epic 3 Story 3.3 | ✓ Covered |
| FR24 | System can default new jobs to score 0 before model learning. | Epic 3 Story 3.3 | ✓ Covered |
| FR25 | System can retrain the relevance model daily. | Epic 3 Story 3.7 | ✓ Covered |
| FR26 | User can mark a job as irrelevant. | Epic 4 Story 4.4 | ✓ Covered |
| FR27 | System can clear a manual label if the job reappears with new wording. | Epic 4 Story 4.4 | ✓ Covered |
| FR28 | User can view "Today" results (new since last run). | Epic 4 Story 4.1 | ✓ Covered |
| FR29 | User can view "All Time" results. | Epic 4 Story 4.1 | ✓ Covered |
| FR30 | User can toggle visibility of irrelevant jobs. | Epic 4 Story 4.5 | ✓ Covered |
| FR31 | System can sort results by first seen time. | Epic 4 Story 4.6 | ✓ Covered |
| FR32 | System can display key fields (title, company, snippet, source, posted date). | Epic 4 Story 4.3 | ✓ Covered |
| FR33 | System can show duplicate count for a canonical item. | Epic 4 Story 4.3 | ✓ Covered |
| FR34 | System can show last run status (success/failed/partial). | Epic 2 Story 2.6 | ✓ Covered |
| FR35 | System can display run summary metrics (trigger time, duration, new jobs count, relevant count). | Epic 2 Story 2.6 | ✓ Covered |
| FR36 | System can surface an error when manual run is blocked by quota. | Epic 2 Story 2.2 | ✓ Covered |
| FR37 | System can log when queries return zero results. | Epic 2 Story 2.6 | ✓ Covered |

### Missing Requirements

- None detected.

### Coverage Statistics

- Total PRD FRs: 37
- FRs covered in epics: 37
- Coverage percentage: 100%

## UX Alignment Assessment

### UX Document Status

Found: /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/ux-design-specification.md

### Alignment Issues

- UX specifies a tri-state label cycle (Relevant -> Irrelevant -> None) while PRD only explicitly requires marking irrelevant and clearing labels. Consider confirming whether "Relevant" is a required user action or UI-only state.

### Warnings

- None blocking; UX and Architecture are generally aligned with PRD scope and constraints.

## Epic Quality Review

### Summary

- Epics are user-value oriented and follow a logical progression.
- No forward dependencies detected across epics or within stories.
- Story sizing is generally reasonable for single-agent delivery.

### 🔴 Critical Violations

- None detected.

### 🟠 Major Issues

1) Story 1.1 (Set up initial project from starter template)
- Issue: Resolved. Story now includes explicit build, startup, and health check criteria.
- Impact: None.
- Recommendation: None.

2) Story 3.5 (Parallel candidate training and evaluation)
- Issue: Resolved. Story now specifies an async job queue with explicit evalWorkers concurrency.
- Impact: None.
- Recommendation: None.

### 🟡 Minor Concerns

1) Story 4.1 (Today and All Time results views)
- Issue: "prior selection preserved when possible" is vague.
- Recommendation: Define concrete conditions for preservation or fallback behavior.

2) Greenfield best-practice note
- Issue: No explicit CI/CD setup story despite greenfield guidance.
- Recommendation: Document intentional deferral in epics or add a post-MVP story if still desired.

3) Story 1.1 developer focus
- Issue: Story is developer-focused rather than direct end-user value.
- Recommendation: Acceptable for greenfield setup, but keep scope minimal and explicitly tied to enabling MVP flows.

## Summary and Recommendations

### Overall Readiness Status

READY (with minor follow-ups)

### Critical Issues Requiring Immediate Action

1) Story 1.1 lacks explicit dependency installation and initial configuration steps required by the starter template guidance.
2) Story 3.5 defines parallel evaluation ambiguously, making it non-testable as written.

### Recommended Next Steps

1. Confirm whether a "Relevant" label action is required (UX vs PRD alignment) and update PRD/epics accordingly.
2. Clarify "selection preserved" behavior in Story 4.1 to remove ambiguity.
3. Decide whether CI/CD remains deferred; document that decision or add a backlog story.

### Final Note

This assessment identified 6 issues across 3 categories (UX alignment, major issues, minor concerns). Major issues have been resolved; address remaining minor items as time allows.

**Assessor:** BMad Master (PM/SM)
