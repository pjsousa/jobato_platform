---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics']
inputDocuments:
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/prd.md
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/architecture.md
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/ux-design-specification.md
---

# jobato - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for jobato, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

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

### NonFunctional Requirements

NFR1: Today/All Time views load within 2 seconds for typical daily result sets.
NFR2: Scheduled or manual runs succeed at least 95% of the time.
NFR3: Failed runs are reported with a visible status indicator.
NFR4: Data is encrypted at rest and in transit.
NFR5: No authentication required in MVP (local use).
NFR6: Target WCAG AA compliance (baseline).
NFR7: SPA frontend with simple, responsive UI.
NFR8: Modern browser support only; latest two versions of Chrome, Firefox, Safari, Edge.
NFR9: No SEO requirements.
NFR10: Focus on fast page load and low-friction review flows.
NFR11: Daily runs complete by 08:00 with results ready for review.
NFR12: Manual runs complete without exceeding quota limits.
NFR13: Precision/recall achieves zero false positives and zero false negatives for daily results.

### Additional Requirements

- Architecture: Use multi-service baseline starter (Vite + React + TypeScript frontend, Spring Boot API Java 17 Gradle, FastAPI ML). Project initialization using these commands is the first implementation story.
- Architecture: Local-first Docker Compose deployment with shared config and data volumes.
- Architecture: Service boundaries use top-level folders: frontend/, api/, ml/, infra/, config/, data/, scripts/.
- Architecture: Redis Streams for ML <-> API events with at-least-once delivery, idempotent consumers, and event envelope (eventId, eventType, eventVersion, occurredAt, runId, payload).
- Architecture: SQLite multi-file per ML run with pointer file (current-db.txt); ML writes new copy then swaps pointer; API reads/writes active DB; no concurrent writes.
- Architecture: Raw/canonical HTML stored outside SQLite; SQLite stores post-processed data and metadata.
- Architecture: API conventions REST + JSON under /api, RFC 7807 Problem Details, and OpenAPI docs.
- Architecture: ML -> API uses API key header; browser -> API uses HTTPS (self-signed locally); no UI auth in MVP; secrets via env or Docker secrets.
- Architecture: Frontend uses React Router, TanStack Query for server state, react-window for list virtualization, and route-based code splitting.
- Architecture: Structured JSON logs; health/metrics endpoints via Actuator/Micrometer (API) and prometheus-client (ML).
- UX: Desktop-first web app; no mobile app requirement; optimized for laptop mouse/keyboard use.
- UX: Two-pane layout (ranked list left, detail right) at >=1024px; stack list above detail below 1024px; basic fallback below 768px.
- UX: Today view loads with top-ranked job selected; list highlights active item.
- UX: Title click cycles state Relevant -> Irrelevant -> None; list state pills only when labeled; title background reflects state.
- UX: Toggle show/hide irrelevant; tabs for Today and All Time.
- UX: Run summary bar shows last run time, new count, relevant count, quota remaining; clear run status and empty-state messaging for zero results.
- UX: Keyboard-accessible list selection and title toggle; visible focus indicators; hit targets >=44px; maintain WCAG AA contrast.

### FR Coverage Map

FR1: Epic 1 - Configure search queries
FR2: Epic 1 - Enable/disable query strings
FR3: Epic 1 - Define allowlisted domains
FR4: Epic 1 - Enable/disable allowlist domains
FR5: Epic 1 - Generate per-site query combinations
FR6: Epic 2 - Manual run trigger
FR7: Epic 2 - Concurrency control for runs
FR8: Epic 2 - Quota enforcement during runs
FR9: Epic 2 - Prevent overlapping runs
FR10: Epic 2 - Record run lifecycle timestamps
FR11: Epic 2 - Fetch search results per query x allowlist
FR12: Epic 2 - Follow single redirect
FR13: Epic 2 - Ignore 404 results
FR14: Epic 2 - Store result metadata
FR15: Epic 2 - Store raw HTML
FR16: Epic 2 - Extract visible text
FR17: Epic 2 - Enforce 1-week revisit throttle
FR18: Epic 2 - Cache search results (12-hour TTL)
FR19: Epic 3 - Normalize URLs for dedupe
FR20: Epic 3 - Detect duplicates via URL + text similarity
FR21: Epic 3 - Link duplicates to canonical record
FR22: Epic 3 - Hide duplicates by default
FR23: Epic 3 - Assign relevance score
FR24: Epic 3 - Default score to 0
FR25: Epic 3 - Daily model retraining
FR26: Epic 4 - Mark job as irrelevant
FR27: Epic 4 - Clear manual label on reappearance
FR28: Epic 4 - Today results view
FR29: Epic 4 - All Time results view
FR30: Epic 4 - Toggle irrelevant visibility
FR31: Epic 4 - Sort by first seen time
FR32: Epic 4 - Display key fields in UI
FR33: Epic 4 - Show duplicate count
FR34: Epic 2 - Show last run status
FR35: Epic 2 - Display run summary metrics
FR36: Epic 2 - Error when run blocked by quota
FR37: Epic 2 - Log zero-result queries

## Epic List

### Epic 1: Configure Search Scope
Users define and control what gets searched through queries and allowlists.
**FRs covered:** FR1, FR2, FR3, FR4, FR5

### Epic 2: Run & Capture Results
Users can run the pipeline and the system captures results reliably within quota and run-status constraints.
**FRs covered:** FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR34, FR35, FR36, FR37

### Epic 3: Result Quality Automation
Results are deduped and scored so the review list is higher quality by default.
**FRs covered:** FR19, FR20, FR21, FR22, FR23, FR24, FR25

### Epic 4: Daily Review & Feedback UX
Users review Today/All Time results, label relevance, and manage visibility of irrelevant items.
**FRs covered:** FR26, FR27, FR28, FR29, FR30, FR31, FR32, FR33

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Acceptance Criteria:**

<!-- for each AC on this story -->

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}
**And** {{additional_criteria}}

<!-- End story repeat -->
