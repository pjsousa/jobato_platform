package com.jobato.api.messaging;

import com.jobato.api.dto.RunRequestedPayload;

import java.time.Instant;

public interface RunEventPublisher {
    void publishRunRequested(String runId, RunRequestedPayload payload, Instant occurredAt);
}
