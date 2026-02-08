package com.jobato.api.model;

import java.time.Instant;

public class RunSummary {
    private final String runId;
    private final Instant triggerTime;
    private final Long durationMs;
    private final Integer newJobsCount;
    private final Integer relevantCount;
    private final String status;

    public RunSummary(String runId, Instant triggerTime, Long durationMs, Integer newJobsCount, Integer relevantCount, String status) {
        this.runId = runId;
        this.triggerTime = triggerTime;
        this.durationMs = durationMs;
        this.newJobsCount = newJobsCount;
        this.relevantCount = relevantCount;
        this.status = status;
    }

    public String getRunId() {
        return runId;
    }

    public Instant getTriggerTime() {
        return triggerTime;
    }

    public Long getDurationMs() {
        return durationMs;
    }

    public Integer getNewJobsCount() {
        return newJobsCount;
    }

    public Integer getRelevantCount() {
        return relevantCount;
    }

    public String getStatus() {
        return status;
    }
}