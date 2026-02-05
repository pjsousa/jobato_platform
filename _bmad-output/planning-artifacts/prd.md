---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments:
  - /Users/pedro/Dev/jobato/_bmad-output/planning-artifacts/product-brief-jobato-2026-02-05.md
  - /Users/pedro/Dev/jobato/_bmad-output/analysis/brainstorming-session-2026-02-04.md
workflowType: 'prd'
briefCount: 1
researchCount: 0
brainstormingCount: 1
projectDocsCount: 0
date: 2026-02-05
author: Pedro
classification:
  projectType: web_app
  domain: general
  complexity: low
  projectContext: greenfield
---

# Product Requirements Document - {{project_name}}

**Author:** {{user_name}}
**Date:** {{date}}

## Success Criteria

### User Success

- Users see zero false positives and zero false negatives in daily results.
- Users submit at least one job application per day, growing to three per day long-term.

### Business Success

- None defined.

### Technical Success

- Daily runs complete by 08:00 with results ready for review.
- Manual runs complete without exceeding quota limits.

### Measurable Outcomes

- Precision/recall achieves zero false positives and zero false negatives for daily results.
- Daily applications: >= 1 per user per day (near-term); >= 3 per day (long-term).
- Run completion time: finishes by 08:00.

## Product Scope

### MVP - Minimum Viable Product

- Manual trigger for the scraper that runs all configured queries against all allowlisted sites.
- Relevance model that produces a score after 1 day of data and retrains daily.
- Simple web UI for reviewing results.

### Growth Features (Post-MVP)

- Scheduled runs.
- Quota limit controls.
- Advanced UI filtering beyond basics.
- Dedupe controls and observability tooling.

### Vision (Future)

- Fully scheduled nightly runs with quota-aware execution.
- Rich dedupe controls and transparency/observability.
- More advanced UI filtering and prioritization.
- Stronger relevance learning from feedback over time.

## User Journeys

### Primary User - Senior/Lead Engineer (Success Path)

**Opening Scene:** A busy senior/lead engineer wants new opportunities but lacks time for daily job searches.
**Rising Action:** They add custom queries and allowlisted platforms, then run the scraper.
**Climax:** The next day, jobato surfaces relevant roles without noise; they apply immediately.
**Resolution:** Reviewing leads becomes a short daily routine and the model reflects their preferences.

### Primary User - Senior/Lead Engineer (Edge Case / Recovery)

**Opening Scene:** A run returns zero results or mostly irrelevant ones.
**Rising Action:** They adjust queries/keywords and rerun within quota limits.
**Climax:** The system returns better results after small changes.
**Resolution:** The engineer trusts the feedback loop and keeps refining.

### Journey Requirements Summary

- Configurable queries and allowlisted domains.
- Manual run control with immediate results display.
- Today view with default focus on new results.
- Fast relevance feedback (mark irrelevant) and model retraining loop.
- Clear empty-state messaging and quick recovery guidance when results are poor.

## Web App Specific Requirements

### Project-Type Overview

Jobato is a SPA web application with a backend API/data pipeline, optimized for fast daily review rather than public SEO.

### Technical Architecture Considerations

- SPA frontend with simple, responsive UI.
- Modern browser support only (no legacy/IE).
- No SEO requirements.
- Real-time features deferred post-MVP.

### Browser Support

- Latest two versions of Chrome, Firefox, Safari, Edge.

### SEO Strategy

- Not required.

### Accessibility

- Target WCAG AA compliance (baseline).

### Implementation Considerations

- Focus on fast page load and low-friction review flows.
- Defer websocket/live updates until post-MVP.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP
**Resource Requirements:** Solo developer (full-stack + data pipeline + basic ML)

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Discovery -> onboarding/config -> daily use -> relevance feedback -> success moment

**Must-Have Capabilities:**
- Manual trigger scraper (queries x allowlist sites)
- Basic data capture (metadata + HTML + visible text)
- Relevance scoring (daily retrain; default 0 initially)
- UI for Today/All Time with irrelevant toggle
- Deduping on URL + text similarity with duplicate_of linkage

### Post-MVP Features

**Phase 2 (Post-MVP):**
- Scheduled runs
- Quota limit controls
- Advanced UI filtering
- Dedupe controls and observability
- Real-time updates

**Phase 3 (Expansion):**
- Rich relevance learning and model tuning
- Enhanced pipeline reliability and monitoring
- Broader query prioritization/optimization
- Additional UI experiences for fast review

### Risk Mitigation Strategy

- Technical: Google API quota limits or result volatility; mitigate with strict quota accounting, caching, and deterministic query ordering.
- Market: Results still feel irrelevant; mitigate with manual feedback loop, query tuning, and optimistic defaults.
- Resource: Solo dev bandwidth; mitigate with strict MVP scope and deferred non-essential features.

## Functional Requirements

### Query & Allowlist Configuration

- FR1: User can define and edit query strings.
- FR2: User can enable or disable individual queries.
- FR3: User can define and edit an allowlist of domains.
- FR4: User can enable or disable individual allowlist domains.
- FR5: System can generate per-site queries by combining query strings with allowlisted domains.

### Run Orchestration

- FR6: User can trigger a run manually.
- FR7: System can limit concurrent query execution based on a global setting.
- FR8: System can stop issuing new API calls when the daily quota limit is reached.
- FR9: System can prevent overlapping runs when one is already in progress.
- FR10: System can record run start and completion timestamps.

### Ingestion & Data Capture

- FR11: System can fetch Google Search results for each query x allowlist pair.
- FR12: System can follow a single redirect for result URLs.
- FR13: System can ignore results with 404 responses.
- FR14: System can store job result metadata (title, snippet, domain, query string, timestamps).
- FR15: System can store the raw HTML for visited job pages.
- FR16: System can extract and store visible text from job pages.
- FR17: System can avoid revisiting a job URL for at least one week.
- FR18: System can cache search results with a 12-hour TTL.

### Deduplication & Canonicalization

- FR19: System can normalize URLs to create a stable dedupe key.
- FR20: System can detect duplicates using URL and text similarity.
- FR21: System can link duplicates to a canonical record.
- FR22: System can hide duplicate records by default while preserving them.

### Relevance Scoring & Feedback

- FR23: System can assign a relevance score from -1 to 1 for each job.
- FR24: System can default new jobs to score 0 before model learning.
- FR25: System can retrain the relevance model daily.
- FR26: User can mark a job as irrelevant.
- FR27: System can clear a manual label if the job reappears with new wording.

### Results Review UI

- FR28: User can view "Today" results (new since last run).
- FR29: User can view "All Time" results.
- FR30: User can toggle visibility of irrelevant jobs.
- FR31: System can sort results by first seen time.
- FR32: System can display key fields (title, company, snippet, source, posted date).
- FR33: System can show duplicate count for a canonical item.

### Run Reporting & Status

- FR34: System can show last run status (success/failed/partial).
- FR35: System can display run summary metrics (trigger time, duration, new jobs count, relevant count).
- FR36: System can surface an error when manual run is blocked by quota.
- FR37: System can log when queries return zero results.

## Non-Functional Requirements

### Performance

- Today/All Time views load within 2 seconds for typical daily result sets.

### Reliability

- Scheduled or manual runs succeed at least 95% of the time.
- Failed runs are reported with a visible status indicator.

### Security

- Data is encrypted at rest and in transit.
- No authentication required in MVP (local use).

### Accessibility

- Target WCAG AA compliance (baseline).
