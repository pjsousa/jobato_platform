package com.jobato.api.messaging;

import java.time.Instant;

public record RunEventEnvelope(
    String eventId,
    String eventType,
    int eventVersion,
    Instant occurredAt,
    String runId,
    String payload
) {
}
