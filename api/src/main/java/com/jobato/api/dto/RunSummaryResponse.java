package com.jobato.api.dto;

import java.time.Instant;

public class RunSummaryResponse {
    private final String runId;
    private final String status;
    private final String triggerTime;
    private final Long durationMs;
    private final Integer newJobsCount;
    private final Integer relevantCount;

    public RunSummaryResponse(String runId, String status, String triggerTime, Long durationMs, Integer newJobsCount, Integer relevantCount) {
        this.runId = runId;
        this.status = status;
        this.triggerTime = triggerTime;
        this.durationMs = durationMs;
        this.newJobsCount = newJobsCount;
        this.relevantCount = relevantCount;
    }

    public String getRunId() {
        return runId;
    }

    public String getStatus() {
        return status;
    }

    public String getTriggerTime() {
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
}