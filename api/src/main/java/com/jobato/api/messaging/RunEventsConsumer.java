package com.jobato.api.messaging;

import com.jobato.api.repository.RunRepository;
import com.jobato.api.service.ReportService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Map;

@Component
public class RunEventsConsumer implements StreamListener<String, MapRecord<String, String, String>> {
    private static final Logger logger = LoggerFactory.getLogger(RunEventsConsumer.class);
    private static final String EVENT_COMPLETED = "run.completed";
    private static final String EVENT_FAILED = "run.failed";
    private static final String STATUS_COMPLETED = "completed";
    private static final String STATUS_FAILED = "failed";
    private static final String STATUS_PARTIAL = "partial";

    private final RunRepository runRepository;
    private final ObjectMapper objectMapper;
    private final ReportService reportService;

    public RunEventsConsumer(RunRepository runRepository, ObjectMapper objectMapper, ReportService reportService) {
        this.runRepository = runRepository;
        this.objectMapper = objectMapper;
        this.reportService = reportService;
    }

    @Override
    public void onMessage(MapRecord<String, String, String> message) {
        RunEventEnvelope event = parse(message.getValue());
        if (event == null) {
            return;
        }
        handleEvent(event);
    }

    public void handleEvent(RunEventEnvelope event) {
        if (EVENT_COMPLETED.equals(event.eventType())) {
            CompletionDetails details = resolveCompletionDetails(event.payload());
            applyStatusUpdate(event, details.status(), details.reason());
        } else if (EVENT_FAILED.equals(event.eventType())) {
            applyStatusUpdate(event, STATUS_FAILED, null);
        } else {
            logger.debug("Ignoring run event type {}", event.eventType());
        }
    }

    private void applyStatusUpdate(RunEventEnvelope event, String status, String statusReason) {
        boolean updated = runRepository.updateRunStatusIfRunning(event.runId(), status, statusReason, event.occurredAt());
        if (!updated) {
            logger.info("Run {} already updated for event {}", event.runId(), event.eventType());
        }
    }

    private CompletionDetails resolveCompletionDetails(String payload) {
        if (payload == null || payload.isBlank()) {
            return new CompletionDetails(STATUS_COMPLETED, null);
        }
        try {
            JsonNode node = objectMapper.readTree(payload);
            String status = readText(node, "status");
            if (STATUS_PARTIAL.equals(status)) {
                return new CompletionDetails(STATUS_PARTIAL, readText(node, "reason"));
            }
        } catch (Exception exception) {
            logger.warn("Failed to parse run completion payload", exception);
        }
        return new CompletionDetails(STATUS_COMPLETED, null);
    }

    private String readText(JsonNode node, String field) {
        JsonNode value = node.get(field);
        if (value == null || value.isNull()) {
            return null;
        }
        return value.asText();
    }

    private record CompletionDetails(String status, String reason) {
    }

    private RunEventEnvelope parse(Map<String, String> fields) {
        try {
            String eventId = fields.get("eventId");
            String eventType = fields.get("eventType");
            String eventVersionValue = fields.get("eventVersion");
            String occurredAtValue = fields.get("occurredAt");
            String runId = fields.get("runId");
            String payload = fields.get("payload");
            if (eventId == null || eventType == null || eventVersionValue == null || occurredAtValue == null || runId == null) {
                logger.warn("Skipping run event missing required fields: {}", fields.keySet());
                return null;
            }
            int eventVersion = Integer.parseInt(eventVersionValue);
            Instant occurredAt = Instant.parse(occurredAtValue);
            return new RunEventEnvelope(eventId, eventType, eventVersion, occurredAt, runId, payload);
        } catch (Exception exception) {
            logger.warn("Failed to parse run event", exception);
            return null;
        }
    }
}
