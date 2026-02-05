---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'Daily Google-query-driven job discovery crawler/parser with allowlisted sites, deduplication, and relevance filtering'
session_goals: 'Surface new relevant job posts daily, suppress duplicates/irrelevant posts, and present results in a simple web UI'
selected_approach: 'AI-Recommended Techniques'
techniques_used: ['Question Storming', 'Morphological Analysis', 'Reverse Brainstorming']
ideas_generated: ['Key decisions and safeguards captured from live session']
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** {{user_name}}
**Date:** {{date}}

## Session Overview

**Topic:** Daily Google-query-driven job discovery crawler/parser with allowlisted sites, deduplication, and relevance filtering
**Goals:** Surface new relevant job posts daily, suppress duplicates/irrelevant posts, and present results in a simple web UI

### Context Guidance

_No additional context file provided._

### Session Setup

We will explore divergent idea spaces across product, technical, data, and UX angles to generate a broad set of options before converging.

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Daily Google-query-driven job discovery crawler/parser with allowlisted sites, deduplication, and relevance filtering with focus on surfacing new relevant jobs daily, suppressing duplicates/irrelevant posts, and presenting results in a simple web UI

**Recommended Techniques:**

- **Question Storming:** Expand unknowns and decision points before solutioning.
- **Morphological Analysis:** Systematically explore combinations across data, scheduling, dedupe, relevance, storage, and UI.
- **Reverse Brainstorming:** Expose failure modes to drive safeguards and quality controls.

**AI Rationale:** The problem is complex with many interdependent choices; we start by opening the question space, then map structured options, and finish by stress-testing the pipeline through failure-first thinking.

## Session Outputs (Captured Summary)

### Product Goal and Constraints

- Daily Google-query-driven job discovery for allowlisted sites with dedupe and relevance filtering.
- Runs nightly at 10pm; results ready by ~08:00; manual run allowed if within quota.
- Query expansion = query x allowlist domain; stop issuing calls when daily quota reached.
- Today = new since last run; global across all queries.
- No auth; local UI; config file only.

### Data, Dedupe, and Scoring

- Store metadata + raw HTML + cleaned visible text.
- Dedupe: URL normalization + text similarity; canonical by first seen.
- Duplicates stored as duplicate_of and hidden by default with a count.
- Relevance score range -1..1; default 0 initially; irrelevant stays visible via toggle.
- If irrelevant item reappears, clear manual label and re-score next day.

### UI and Review Flow

- Views: Today + All Time; toggle irrelevant; sort by first seen.
- Minimal fields: title, company, snippet, source, posted date.
- Run summary: triggered time, duration, new jobs, relevant count.

### Execution and Safety Decisions

- Limited parallelism configured globally; single writer to SQLite.
- Cache TTL 12 hours; do not revisit job URLs for at least one week.
- Follow one redirect only; drop 404s.

### Safeguards (Reverse Brainstorming)

- Pre-compute call budget; hard stop on quota; mark run partial when stopped.
- Run lock to prevent overlap; manual run refused when active.
- Config validation with warnings; allowlist subdomain expansion tests.
- Canonical upgrade if richer duplicate exists.
- If zero results across all queries, mark run failed.
- HTML fetch failures handled gracefully; still store metadata.

### Detailed Notes from Session (Full Capture)

#### Sources and Querying

- Query source: Google queries via a custom Google Search API call.
- Allowlist: workable.com, teamtailor.com, greenhouse.io (include all subdomains/paths under these hostnames).
- Query examples: "python AND software AND engineer AND lead AND remote", "Remote AND lead AND engineer".
- Query composition: system generates the site: part for each allowlist site on each configured query.
- Each query is paired with each allowlist site until daily free quota is reached.
- Region focus: user will encode region in the query (priority: Europe > worldwide > Portugal).

#### Scheduling and Cadence

- Runs daily at 10pm; processing can run overnight as long as results are ready by 08:00.
- Manual run is allowed but must never exceed quota; if quota reached, stop and surface UI error.
- Running nightly-only is acceptable.
- If quota is reached mid-run, jobato must stop issuing new calls immediately (service keeps running).

#### Definition of New and Time Windows

- New = not seen before AND posted within 30 days (leveraging Google time-bound query filter).
- Today view is "new since last run".
- "New since last run" is global across all queries.

#### Deduplication and Duplicates

- Duplicate definition: same URL OR same job text across multiple sites from the same company.
- Store duplicates with a reference to a canonical "duplicate_of" job.
- Canonical choice: first seen by default.
- Dedupe approaches should be implemented within the service (Jaccard/Levenshtein/Hamming/MinHash acceptable; choose what scales best).
- URL normalization/hashing is required for basic dedupe.

#### Relevance and Labels

- Default label is optimistic: Relevant until model learns.
- Irrelevant items should be shown but visually de-emphasized.
- Irrelevant feedback is per job (not per query or per domain).
- If a job reappears with new wording after being marked irrelevant, remove manual classification and re-score next day.
- Relevance score range: -1 (irrelevant) to 1 (relevant); score can start at 0 and be noisy initially.

#### UI Workflow

- Tabs: Today + All Time.
- Today is default filter.
- Toggle to show/hide irrelevant items.
- Primary action: review leads quickly.
- Show duplicates count and hide duplicates by default.
- Fields for fast review: title, company, snippet, source, posted date.
- Delivery: simple web UI, results ready when accessed.

#### Data Capture and Parsing

- MVP does not require full scraping, but later can extract visible text from HTML for dedupe/scoring.
- Store raw HTML and cleaned visible text for future relevance learning.
- Redirect handling: follow first redirect only; ignore 404s.

#### Caching and Revisit Rules

- Cache Google results with TTL 12 hours.
- Do not revisit job URLs already visited within the last week.

#### Storage and Deployment

- SQLite + files.
- Runs locally; dockerized is acceptable.
- Scheduling handled inside the service (no cron).

#### Failure Handling and Logging

- If zero results found, log this explicitly.
- If API quota reached, stop issuing new calls immediately.
- If Google API is down, mark run failed and wait for next schedule.
- Run summary required: triggered time, duration, new jobs count, relevant count.

#### Open / Deferred Decisions

- Logging/reporting specifics were deferred (to be decided).
- Query prioritization beyond deterministic ordering deferred for MVP.
