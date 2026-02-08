package com.jobato.api.messaging;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.jobato.api.dto.RunRequestedPayload;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@Component
public class RedisRunEventPublisher implements RunEventPublisher {
    private static final String STREAM_KEY = "ml:run-events";
    private static final int EVENT_VERSION = 1;

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final Clock clock;

    public RedisRunEventPublisher(StringRedisTemplate redisTemplate, ObjectMapper objectMapper, Clock clock) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.clock = clock;
    }

    @Override
    public void publishRunRequested(String runId, RunRequestedPayload payload, Instant occurredAt) {
        String eventId = UUID.randomUUID().toString();
        Instant eventTime = occurredAt == null ? Instant.now(clock) : occurredAt;
        String payloadJson = serializePayload(payload);

        Map<String, String> fields = new LinkedHashMap<>();
        fields.put("eventId", eventId);
        fields.put("eventType", "run.requested");
        fields.put("eventVersion", String.valueOf(EVENT_VERSION));
        fields.put("occurredAt", eventTime.toString());
        fields.put("runId", runId);
        fields.put("payload", payloadJson);

        redisTemplate.opsForStream().add(StreamRecords.mapBacked(fields).withStreamKey(STREAM_KEY));
    }

    private String serializePayload(RunRequestedPayload payload) {
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Failed to serialize run requested payload", exception);
        }
    }
}
