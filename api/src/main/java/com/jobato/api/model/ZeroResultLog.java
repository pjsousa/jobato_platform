package com.jobato.api.model;

import java.time.Instant;

public record ZeroResultLog(
    String runId,
    String queryText,
    String domain,
    Instant occurredAt
) {
}
