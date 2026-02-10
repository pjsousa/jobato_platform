package com.jobato.api.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.jobato.api.model.RunRecord;
import com.jobato.api.repository.ActiveRunDatabase;
import com.jobato.api.repository.RunRepository;
import com.jobato.api.service.ReportService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;

import static org.assertj.core.api.Assertions.assertThat;

class RunEventsConsumerTest {
    @TempDir
    Path tempDir;

    private RunRepository runRepository;
    private RunEventsConsumer runEventsConsumer;

    @BeforeEach
    void setup() throws Exception {
        Path dataDir = tempDir.resolve("data");
        Path dbDir = dataDir.resolve("db/runs");
        Files.createDirectories(dbDir);
        Path pointer = dataDir.resolve("db/current-db.txt");
        Files.createDirectories(pointer.getParent());
        Files.writeString(pointer, dbDir.resolve("runs-test.db").toString());

        ActiveRunDatabase activeRunDatabase = new ActiveRunDatabase(dataDir.toString());
        runRepository = new RunRepository(activeRunDatabase);
        ReportService reportService = org.mockito.Mockito.mock(ReportService.class);
        runEventsConsumer = new RunEventsConsumer(runRepository, new ObjectMapper(), reportService);
    }

    @Test
    void updatesRunStatusWhenCompletedEventArrives() {
        RunRecord created = runRepository.createRun("run-1", Instant.parse("2026-02-07T10:00:00Z"));
        RunEventEnvelope event = new RunEventEnvelope(
            "event-1",
            "run.completed",
            1,
            Instant.parse("2026-02-07T10:10:00Z"),
            created.runId(),
            "{}"
        );

        runEventsConsumer.handleEvent(event);

        RunRecord updated = runRepository.findById(created.runId()).orElseThrow();
        assertThat(updated.status()).isEqualTo("completed");
        assertThat(updated.endedAt()).isEqualTo(event.occurredAt());
        assertThat(updated.statusReason()).isNull();
    }

    @Test
    void ignoresDuplicateFailedEvents() {
        RunRecord created = runRepository.createRun("run-2", Instant.parse("2026-02-07T11:00:00Z"));
        RunEventEnvelope event = new RunEventEnvelope(
            "event-2",
            "run.failed",
            1,
            Instant.parse("2026-02-07T11:05:00Z"),
            created.runId(),
            "{}"
        );

        runEventsConsumer.handleEvent(event);
        runEventsConsumer.handleEvent(new RunEventEnvelope(
            "event-3",
            "run.failed",
            1,
            Instant.parse("2026-02-07T11:10:00Z"),
            created.runId(),
            "{}"
        ));

        RunRecord updated = runRepository.findById(created.runId()).orElseThrow();
        assertThat(updated.status()).isEqualTo("failed");
        assertThat(updated.endedAt()).isEqualTo(event.occurredAt());
        assertThat(updated.statusReason()).isNull();
    }

    @Test
    void storesPartialStatusAndReasonFromCompletionPayload() {
        RunRecord created = runRepository.createRun("run-3", Instant.parse("2026-02-07T12:00:00Z"));
        RunEventEnvelope event = new RunEventEnvelope(
            "event-4",
            "run.completed",
            1,
            Instant.parse("2026-02-07T12:05:00Z"),
            created.runId(),
            "{\"status\":\"partial\",\"reason\":\"quota-reached\"}"
        );

        runEventsConsumer.handleEvent(event);

        RunRecord updated = runRepository.findById(created.runId()).orElseThrow();
        assertThat(updated.status()).isEqualTo("partial");
        assertThat(updated.statusReason()).isEqualTo("quota-reached");
    }
}
