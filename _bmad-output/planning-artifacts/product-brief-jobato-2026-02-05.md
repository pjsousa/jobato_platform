---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - /Users/pedro/Dev/jobato/_bmad-output/analysis/brainstorming-session-2026-02-04.md
date: 2026-02-05
author: Pedro
---

# Product Brief: {{project_name}}

<!-- Content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

Jobato is a daily, personalized job discovery tool for busy senior and lead software engineers who do not have time to manually search and evaluate postings. It surfaces the most relevant new opportunities on the day they are posted, using a custom, user-trained relevance model and an allowlisted Google query pipeline. The goal is to reduce wasted time on misleading job posts while providing a highly tailored, cost-effective alternative to paywalled services.

---

## Core Vision

### Problem Statement

Busy senior and lead engineers need a way to discover high-quality job opportunities daily without spending time searching, clicking through listings, and reading posts that turn out to be irrelevant.

### Problem Impact

Today, engineers spend significant time reviewing promising-looking postings that do not match their preferences, leading to wasted time and missed opportunities. Over time, this contributes to staying in unfulfilling jobs longer than necessary.

### Why Existing Solutions Fall Short

Current job boards, alerts, and aggregators do not allow deep, personalized relevance training, and when customization exists it is often behind paywalls. This leaves experienced engineers without a fast, affordable way to filter for truly relevant roles.

### Proposed Solution

Jobato runs daily Google-based searches over an allowlisted set of job platforms and uses user-trained relevance scoring to surface the most relevant new posts. It prioritizes speed, customization, and a simple UI that enables quick review of leads.

### Key Differentiators

- User-trained relevance model on public URLs for deeply tailored results.
- Cost-effective, local-first approach without paywalls.
- Focus on surfacing the single most relevant daily opportunity for senior/lead engineers.

## Target Users

### Primary Users

**Primary Persona: Senior/Lead Software Engineer (Job Seeker)**

- **Context:** Busy senior/lead engineer actively exploring new opportunities; relies on manual Google searches and LinkedIn alerts.
- **Goals:** Find highly relevant roles quickly; minimize time spent on misleading listings; see the best opportunities on the day they are posted.
- **Pain Points:** Promising titles/companies often turn out irrelevant; paywalled tools limit deep personalization; daily searching is time-consuming.
- **Motivations:** Escape unfulfilling roles and access better-fit opportunities with minimal time cost.
- **Assumptions to confirm:** Primarily remote or remote-friendly roles; Europe-first search focus; prefers a simple, local-first tool.

### Secondary Users

N/A (single user group: engineers)

### User Journey

1. **Discovery:** Learns about jobato through personal need for daily job leads and a desire to avoid paywalls.
2. **Onboarding:** Adds queries and allowlisted domains; schedules nightly runs; initial default relevance set to optimistic.
3. **Core Usage:** Each morning reviews "Today" results; marks irrelevant items; focuses on the top relevant opportunities first.
4. **Success Moment:** Finds a genuinely relevant role on day one without wasting time on poor-fit listings.
5. **Long-term:** Builds a personalized relevance model that consistently surfaces high-quality leads with minimal daily effort.

## Success Metrics

**User Success**

- Users see zero false positives and zero false negatives in daily results.
- Users submit at least one job application per day.

### Business Objectives

- N/A (no business metrics defined for now).

### Key Performance Indicators

- **Precision/Recall:** 0 false positives and 0 false negatives in daily results.
- **Daily Applications:** >= 1 application per user per day (near-term).
- **Daily Applications (Longer-term):** >= 3 applications per user per day.
- **Model Stability (3-month mark):** Users no longer adjust model classifications.

## MVP Scope

### Core Features

- Manual trigger for the scraper that runs all configured query strings against all configured allowlisted sites.
- Relevance model that produces a score after 1 day of data and can be retrained daily.
- Simple web UI for reviewing results.

### Out of Scope for MVP

- Scheduled runs.
- Quota limit controls.
- Advanced UI filtering beyond basics.
- Dedupe controls and observability tooling.

### MVP Success Criteria

- User can run a manual scrape and see new results in the UI the same day.
- Relevance scoring starts producing non-zero scores after day one and updates daily.
- User can review and act on leads quickly with minimal friction.

### Future Vision

- Fully scheduled nightly runs with quota-aware execution.
- Rich dedupe controls and transparency/observability.
- More advanced UI filtering and prioritization.
- Stronger relevance learning from feedback over time.
