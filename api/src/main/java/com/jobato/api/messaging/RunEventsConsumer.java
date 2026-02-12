package com.jobato.api.messaging;

import com.jobato.api.model.RunRecord;
import com.jobato.api.model.ZeroResultLog;
import com.jobato.api.repository.RunRepository;
import com.jobato.api.service.ReportService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
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
        JsonNode payloadNode = parsePayloadNode(event.payload());
        if (EVENT_COMPLETED.equals(event.eventType())) {
            CompletionDetails details = resolveCompletionDetails(payloadNode);
            boolean updated = applyStatusUpdate(event, details.status(), details.reason());
            if (updated) {
                persistRunReporting(event, details.status(), payloadNode);
            }
        } else if (EVENT_FAILED.equals(event.eventType())) {
            boolean updated = applyStatusUpdate(event, STATUS_FAILED, null);
            if (updated) {
                persistRunReporting(event, STATUS_FAILED, payloadNode);
            }
        } else {
            logger.debug("Ignoring run event type {}", event.eventType());
        }
    }

    private boolean applyStatusUpdate(RunEventEnvelope event, String status, String statusReason) {
        boolean updated = runRepository.updateRunStatusIfRunning(event.runId(), status, statusReason, event.occurredAt());
        if (!updated) {
            logger.info("Run {} already updated for event {}", event.runId(), event.eventType());
        }
        return updated;
    }

    private CompletionDetails resolveCompletionDetails(JsonNode payloadNode) {
        if (payloadNode == null) {
            return new CompletionDetails(STATUS_COMPLETED, null);
        }
        String status = readText(payloadNode, "status");
        if (STATUS_PARTIAL.equals(status)) {
            return new CompletionDetails(STATUS_PARTIAL, readText(payloadNode, "reason"));
        }
        return new CompletionDetails(STATUS_COMPLETED, null);
    }

    private JsonNode parsePayloadNode(String payload) {
        if (payload == null || payload.isBlank()) {
            return null;
        }
        try {
            return objectMapper.readTree(payload);
        } catch (Exception exception) {
            logger.warn("Failed to parse run event payload", exception);
            return null;
        }
    }

    private void persistRunReporting(RunEventEnvelope event, String status, JsonNode payloadNode) {
        RunRecord runRecord = runRepository.findById(event.runId()).orElse(null);
        if (runRecord == null) {
            logger.warn("Cannot persist reporting for unknown run {}", event.runId());
            return;
        }

        int newJobsCount = readInt(payloadNode, "newJobsCount", readInt(payloadNode, "persistedResults", 0));
        int relevantCount = readInt(payloadNode, "relevantCount", 0);
        long durationMs = Math.max(0L, Duration.between(runRecord.startedAt(), event.occurredAt()).toMillis());

        reportService.saveRunSummary(
            event.runId(),
            runRecord.startedAt(),
            durationMs,
            newJobsCount,
            relevantCount,
            status
        );

        List<ZeroResultLog> zeroResultLogs = extractZeroResultLogs(event.runId(), payloadNode, event.occurredAt());
        reportService.saveZeroResultLogs(zeroResultLogs);
    }

    private int readInt(JsonNode node, String field, int defaultValue) {
        if (node == null) {
            return defaultValue;
        }
        JsonNode value = node.get(field);
        if (value == null || value.isNull()) {
            return defaultValue;
        }
        if (value.canConvertToInt()) {
            return value.asInt();
        }
        if (value.isTextual()) {
            try {
                return Integer.parseInt(value.asText());
            } catch (NumberFormatException ignored) {
                return defaultValue;
            }
        }
        return defaultValue;
    }

    private List<ZeroResultLog> extractZeroResultLogs(String runId, JsonNode payloadNode, Instant defaultOccurredAt) {
        if (payloadNode == null) {
            return List.of();
        }
        JsonNode zeroResults = payloadNode.get("zeroResults");
        if (zeroResults == null || !zeroResults.isArray()) {
            return List.of();
        }

        List<ZeroResultLog> logs = new ArrayList<>();
        for (JsonNode zeroResultEntry : zeroResults) {
            String queryText = readText(zeroResultEntry, "queryText");
            String domain = readText(zeroResultEntry, "domain");
            if (queryText == null || queryText.isBlank() || domain == null || domain.isBlank()) {
                continue;
            }
            Instant occurredAt = parseOccurredAt(readText(zeroResultEntry, "occurredAt"), defaultOccurredAt);
            logs.add(new ZeroResultLog(runId, queryText.trim(), domain.trim().toLowerCase(), occurredAt));
        }
        return logs;
    }

    private Instant parseOccurredAt(String occurredAtValue, Instant defaultOccurredAt) {
        if (occurredAtValue == null || occurredAtValue.isBlank()) {
            return defaultOccurredAt;
        }
        try {
            return Instant.parse(occurredAtValue);
        } catch (Exception exception) {
            return defaultOccurredAt;
        }
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
