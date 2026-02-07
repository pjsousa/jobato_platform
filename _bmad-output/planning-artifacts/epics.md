---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
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

## Epic 1: Configure Search Scope

Users define and control what gets searched through queries and allowlists.

### Story 1.1: Manage query strings

As a user,
I want to create and edit query strings,
So that I can control the job searches I care about.

**Acceptance Criteria:**

**Given** a valid query string
**When** I add it
**Then** it is persisted and available for runs
**And** it appears in the enabled queries list by default

**Given** an existing query
**When** I edit it
**Then** the updated query is stored and used on subsequent runs
**And** existing run history remains unchanged

**Given** an existing query
**When** I disable it
**Then** it is excluded from run generation
**And** it remains available for re-enable without losing its contents

**Given** a duplicate query text
**When** I try to add it
**Then** the system rejects the duplicate with a clear validation error
**And** no additional query entry is created

### Story 1.2: Manage allowlist domains

As a user,
I want to create and edit allowlisted domains,
So that searches run only on approved sites.

**Acceptance Criteria:**

**Given** a valid domain
**When** I add it
**Then** it is persisted and available for runs
**And** it appears in the enabled allowlist by default

**Given** an existing domain
**When** I edit it
**Then** the updated domain is stored and used on subsequent runs
**And** existing run history remains unchanged

**Given** an existing domain
**When** I disable it
**Then** it is excluded from run generation
**And** it remains available for re-enable without losing its contents

**Given** an invalid domain format
**When** I try to add it
**Then** the system rejects it with a clear validation error
**And** no allowlist entry is created

### Story 1.3: Generate per-site query combinations

As a user,
I want the system to combine enabled queries and allowlisted domains,
So that each run executes per-site searches.

**Acceptance Criteria:**

**Given** enabled queries and allowlisted domains
**When** a run is initiated
**Then** the system generates all query x domain combinations
**And** only enabled queries and domains are included

**Given** a disabled query or domain
**When** a run is initiated
**Then** combinations including it are not generated
**And** the run uses only enabled inputs

**Given** no enabled queries or domains
**When** a run is initiated
**Then** the system returns a clear error and does not proceed
**And** the user is prompted to add or enable queries and domains

## Epic 2: Run & Capture Results

Users can run the pipeline and the system captures results reliably within quota and run-status constraints.

### Story 2.1: Local-first runtime baseline

As a developer,
I want a local multi-service baseline with shared config and data,
So that I can run the system end-to-end and trigger runs locally.

**Acceptance Criteria:**

**Given** the repository is initialized
**When** the baseline scaffold is created
**Then** top-level folders exist (frontend/, api/, ml/, infra/, config/, data/, scripts/)
**And** service skeletons are present for frontend, API, and ML

**Given** docker-compose is started
**When** services are running
**Then** API and ML health endpoints respond
**And** Redis is reachable by both services

**Given** shared volumes are configured
**When** services run
**Then** config/ and data/ are mounted
**And** each service has a .env.example file

**Given** the baseline is up
**When** I verify runtime behavior
**Then** only health checks are required
**And** no business logic is required for this story

### Story 2.2: Manual run request and lifecycle tracking

As a user,
I want to trigger a run and see its lifecycle state,
So that I know when a run starts, finishes, or fails.

**Acceptance Criteria:**

**Given** no run is in progress
**When** I trigger a run
**Then** a run record is created with status "running"
**And** the start timestamp is recorded

**Given** a run is triggered
**When** the system accepts it
**Then** a run.requested event is published to Redis Streams
**And** the event includes runId and event metadata

**Given** a run is already in progress
**When** I trigger another run
**Then** the system rejects it with a clear "run in progress" error
**And** no new run record is created

**Given** ML publishes a run completion or failure event
**When** the API consumes the event
**Then** the run status is updated accordingly
**And** the end timestamp is recorded

### Story 2.3: Quota and concurrency enforcement

As a user,
I want runs to respect concurrency and daily quota limits,
So that I avoid exceeding API limits.

**Acceptance Criteria:**

**Given** configured concurrency and daily quota
**When** a run executes
**Then** concurrent query execution does not exceed the configured limit
**And** the quota counter is updated as calls are made

**Given** the daily quota is already reached
**When** I trigger a run
**Then** the system blocks the run
**And** returns a quota-reached error

**Given** the quota is reached mid-run
**When** additional calls would exceed it
**Then** the system stops issuing new calls
**And** the run is marked partial with a quota-reached reason

### Story 2.4: Fetch search results and persist metadata

As a user,
I want the system to fetch search results for each query x allowlist pair,
So that I can review job opportunities found in the run.

**Acceptance Criteria:**

**Given** enabled queries and allowlisted domains
**When** a run executes
**Then** the system calls Google Search for each query x domain combination
**And** each call is associated with the run ID

**Given** a result URL redirects once
**When** the system fetches it
**Then** it follows a single redirect
**And** stores the final URL

**Given** a 404 response
**When** the system encounters it
**Then** the result is ignored
**And** no record is created for that result

**Given** valid results
**When** they are persisted
**Then** job metadata (title, snippet, domain, query, timestamps) is stored
**And** each result is linked to the run

### Story 2.5: Capture raw HTML and visible text

As a user,
I want raw HTML and visible text captured for each job page,
So that the system can analyze and display content later.

**Acceptance Criteria:**

**Given** a result URL
**When** the system fetches the page
**Then** raw HTML is saved to the file store
**And** the stored path is recorded with the result

**Given** saved HTML
**When** extraction runs
**Then** visible text is extracted and stored
**And** linked to the result record

**Given** a fetch error
**When** it occurs
**Then** the system records the error
**And** continues processing other results

### Story 2.6: Cache results and enforce revisit throttling

As a user,
I want the system to reuse recent results and avoid revisiting the same URL too soon,
So that runs are efficient and within quota.

**Acceptance Criteria:**

**Given** cached results within the 12-hour TTL for a query x domain
**When** a run executes
**Then** cached results are used instead of a new API call
**And** the cache usage is recorded for the run

**Given** a job URL was visited within the last week
**When** a run executes
**Then** the system skips revisiting it
**And** records the skip reason with the result

### Story 2.7: Run summary metrics and zero-results logging

As a user,
I want run summaries and visibility into zero-result queries,
So that I can understand run outcomes and tune inputs.

**Acceptance Criteria:**

**Given** a run completes
**When** metrics are computed
**Then** the system records trigger time, duration, new jobs count, and overall status
**And** relevant count is included (0 if no labels exist yet)

**Given** a query returns zero results
**When** that happens
**Then** the system logs it with query and domain context
**And** the log entry is linked to the run

**Given** a run finishes
**When** I request the last run status
**Then** the latest status and summary metrics are available via the API
**And** the response includes a run identifier

## Epic 3: Result Quality Automation

Results are deduped and scored so the review list is higher quality by default.

### Story 3.1: Normalize URLs for stable dedupe keys

As a user,
I want results normalized into stable URL keys,
So that the system can reliably detect duplicates.

**Acceptance Criteria:**

**Given** a result URL
**When** it is ingested
**Then** a normalized URL key is generated and stored
**And** the key is used for future dedupe checks

**Given** two URLs that differ only by tracking params or casing
**When** they are normalized
**Then** they produce the same normalized key
**And** the raw URL is still preserved

**Given** a result URL that cannot be normalized
**When** normalization fails
**Then** the system records a clear error
**And** dedupe is skipped for that item

### Story 3.2: Detect and link duplicates

As a user,
I want duplicates detected and linked to a canonical result,
So that repeated postings do not clutter review.

**Acceptance Criteria:**

**Given** two results with the same normalized key
**When** dedupe runs
**Then** the later result is linked to the canonical record
**And** the canonical record remains visible by default

**Given** two results with high text similarity
**When** dedupe runs
**Then** they are linked even if URLs differ
**And** the duplicate is flagged hidden by default

**Given** a duplicate is stored
**When** it is retrieved via the API
**Then** it is hidden by default
**And** its canonical link is available for reference

### Story 3.3: Assign relevance scores (baseline)

As a user,
I want each result assigned a relevance score,
So that review is prioritized by likely fit.

**Acceptance Criteria:**

**Given** a new result
**When** it is scored
**Then** it receives a score in the range -1 to 1
**And** the score is stored with the result

**Given** no prior model exists
**When** a result is scored
**Then** the default score is 0
**And** the scoring pipeline completes successfully

**Given** a stored score
**When** results are retrieved
**Then** the score is available for sorting and display
**And** the API returns it in the response payload

### Story 3.4: Pluggable model interface and registry

As a ML developer,
I want the system to load multiple candidate models that follow a scikit-learn style interface,
So that teams can plug in their own models without changing the core pipeline.

**Acceptance Criteria:**

**Given** a model package that implements fit and predict
**When** it is registered
**Then** the system can load it without code changes to the core pipeline
**And** it is available as a selectable candidate

**Given** a registry configuration
**When** the ML service starts
**Then** it discovers all available models
**And** exposes their identifiers for evaluation

**Given** an invalid model module
**When** it is loaded
**Then** the system rejects it with a clear error
**And** continues with other models

### Story 3.5: Parallel candidate training and evaluation

As a user,
I want multiple candidate models trained and evaluated in parallel on the same dataset,
So that I can compare their metrics side-by-side.

**Acceptance Criteria:**

**Given** N registered models
**When** an evaluation run is requested
**Then** all N models are trained on the same labeled dataset and evaluated independently
**And** evaluation jobs run in parallel where possible

**Given** evaluation completes
**When** results are stored
**Then** each model has a metrics record tied to the run ID and model version
**And** the metrics record includes dataset identifiers

**Given** default metrics are required
**When** evaluation runs
**Then** it produces precision, recall, F1, and accuracy
**And** the schema is extensible for additional metrics

### Story 3.6: Model selection and activation

As a user,
I want to view candidate metrics and promote one model to active use,
So that scoring uses the best available model.

**Acceptance Criteria:**

**Given** evaluation results exist
**When** I request comparisons
**Then** I can see each candidate’s metrics for the run
**And** results are grouped by model version

**Given** a candidate is promoted
**When** new results are scored
**Then** the active model is used
**And** its version is recorded with each score

**Given** a previous model is selected again
**When** I switch back
**Then** the system can roll back to that model version
**And** scoring resumes with the selected version

## Epic 4: Daily Review and Feedback UX

Users review Today/All Time results, label relevance, and manage visibility of irrelevant items.

### Story 4.1: Today and All Time results views

As a user,
I want to switch between Today and All Time views,
So that I can focus on new results or review history.

**Acceptance Criteria:**

**Given** results exist
**When** I select Today
**Then** I see only results new since the last run
**And** the list is filtered accordingly

**Given** results exist
**When** I select All Time
**Then** I see the full history of results
**And** the list reflects all stored items

**Given** the view changes
**When** data is loading
**Then** a clear loading state is shown
**And** the prior selection is preserved when possible

### Story 4.2: Two-pane results layout with selection

As a user,
I want a split layout with a ranked list and a detail panel,
So that I can scan quickly and see context.

**Acceptance Criteria:**

**Given** the Today view loads
**When** results are present
**Then** the top-ranked item is selected by default
**And** its details are shown in the right panel

**Given** an item is selected
**When** I navigate the list
**Then** the detail panel updates to the selected item
**And** the list visually highlights the active item

**Given** screen width is below 1024px
**When** the view renders
**Then** the list stacks above the detail panel
**And** selection remains persistent across the layout change

### Story 4.3: Key fields and duplicate count display

As a user,
I want to see key job fields and duplicate counts,
So that I can judge relevance quickly.

**Acceptance Criteria:**

**Given** a result item
**When** it is displayed in the list
**Then** it shows title, company, snippet, source, and posted date
**And** duplicate count is shown when available

**Given** a canonical item
**When** it is displayed in detail
**Then** it shows the duplicate count and canonical linkage
**And** the detail view surfaces the source link

### Story 4.4: Mark job as irrelevant and clear label

As a user,
I want to mark a job as irrelevant and clear the label if needed,
So that my feedback improves results.

**Acceptance Criteria:**

**Given** a selected job
**When** I click the title
**Then** its label cycles Relevant -> Irrelevant -> None
**And** the list state pill updates accordingly

**Given** a label changes
**When** it is saved
**Then** the UI updates immediately
**And** the label is persisted for future runs

**Given** a job reappears
**When** it has a prior label
**Then** the label can be cleared manually
**And** the cleared state is saved

### Story 4.5: Toggle irrelevant visibility

As a user,
I want to hide or show irrelevant items,
So that I can focus on the most relevant results.

**Acceptance Criteria:**

**Given** the toggle is off
**When** a job is labeled irrelevant
**Then** it is hidden from the list
**And** the total count reflects the filtered view

**Given** the toggle is on
**When** irrelevant items exist
**Then** they are shown with de-emphasized styling
**And** their labels remain visible

### Story 4.6: Sort by first seen time

As a user,
I want results sorted by first seen time,
So that the newest items appear first in Today view.

**Acceptance Criteria:**

**Given** results are loaded
**When** the list is rendered
**Then** items are sorted by first seen time descending
**And** the ordering is stable across refreshes

**Given** a user switches views
**When** the list renders
**Then** the sort order remains consistent
**And** the active selection is preserved when possible

### Story 4.7: Accessibility and keyboard interaction

As a user,
I want full keyboard navigation and accessible UI,
So that I can use the app efficiently.

**Acceptance Criteria:**

**Given** the list has focus
**When** I use arrow keys
**Then** selection moves and the detail panel updates
**And** focus remains visible at all times

**Given** the title is focused
**When** I press Enter or Space
**Then** the label cycles
**And** the change is announced to assistive tech

**Given** focus changes
**When** the UI renders
**Then** focus states meet WCAG AA contrast
**And** interactive elements have clear labels
