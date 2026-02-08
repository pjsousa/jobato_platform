package com.jobato.api.dto;

public record RunResponse(
    String runId,
    String status,
    String startedAt,
    String endedAt,
    String statusReason
) {
}
