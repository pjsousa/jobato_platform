package com.jobato.api.model;

import java.time.Instant;

public record RunRecord(
    String runId,
    String status,
    Instant startedAt,
    Instant endedAt,
    String statusReason
) {
}
