package com.jobato.api.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.jobato.api.model.RunRecord;
import com.jobato.api.model.RunSummary;
import com.jobato.api.model.ZeroResultLog;
import com.jobato.api.repository.ActiveRunDatabase;
import com.jobato.api.repository.RunRepository;
import com.jobato.api.repository.RunSummaryRepository;
import com.jobato.api.repository.ZeroResultLogRepository;
import com.jobato.api.service.ReportService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class RunEventsConsumerTest {
    @TempDir
    Path tempDir;

    private RunRepository runRepository;
    private ReportService reportService;
    private RunEventsConsumer runEventsConsumer;

    @BeforeEach
    void setup() throws Exception {
        Path dataDir = tempDir.resolve("data");
        Path dbDir = dataDir.resolve("db/runs");
        Files.createDirectories(dbDir);
        Path pointer = dataDir.resolve("db/current-db.txt");
        Files.createDirectories(pointer.getParent());
        Files.writeString(pointer, dbDir.resolve("runs-test-" + UUID.randomUUID() + ".db").toString());

        ActiveRunDatabase activeRunDatabase = new ActiveRunDatabase(dataDir.toString());
        runRepository = new RunRepository(activeRunDatabase);
        RunSummaryRepository runSummaryRepository = new RunSummaryRepository(activeRunDatabase);
        ZeroResultLogRepository zeroResultLogRepository = new ZeroResultLogRepository(activeRunDatabase);
        reportService = new ReportService(runSummaryRepository, zeroResultLogRepository);
        runEventsConsumer = new RunEventsConsumer(runRepository, new ObjectMapper(), reportService);
    }

    @Test
    void updatesRunStatusAndPersistsSummaryWhenCompletedEventArrives() {
        RunRecord created = runRepository.createRun("run-1", Instant.parse("2026-02-07T10:00:00Z"));
        RunEventEnvelope event = new RunEventEnvelope(
            "event-1",
            "run.completed",
            1,
            Instant.parse("2026-02-07T10:10:00Z"),
            created.runId(),
            "{\"status\":\"completed\",\"newJobsCount\":7,\"relevantCount\":0}"
        );

        runEventsConsumer.handleEvent(event);

        RunRecord updated = runRepository.findById(created.runId()).orElseThrow();
        assertThat(updated.status()).isEqualTo("completed");
        assertThat(updated.endedAt()).isEqualTo(event.occurredAt());
        assertThat(updated.statusReason()).isNull();

        RunSummary summary = reportService.getLatestRunSummary().orElseThrow();
        assertThat(summary.getRunId()).isEqualTo(created.runId());
        assertThat(summary.getStatus()).isEqualTo("completed");
        assertThat(summary.getTriggerTime()).isEqualTo(Instant.parse("2026-02-07T10:00:00Z"));
        assertThat(summary.getDurationMs()).isEqualTo(600000L);
        assertThat(summary.getNewJobsCount()).isEqualTo(7);
        assertThat(summary.getRelevantCount()).isEqualTo(0);
    }

    @Test
    void ignoresDuplicateFailedEventsAndKeepsSingleSummaryRow() {
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

        RunSummary summary = reportService.getLatestRunSummary().orElseThrow();
        assertThat(summary.getRunId()).isEqualTo(created.runId());
        assertThat(summary.getStatus()).isEqualTo("failed");
        assertThat(summary.getDurationMs()).isEqualTo(300000L);
    }

    @Test
    void storesPartialStatusReasonAndSummaryMetricsFromCompletionPayload() {
        RunRecord created = runRepository.createRun("run-3", Instant.parse("2026-02-07T12:00:00Z"));
        RunEventEnvelope event = new RunEventEnvelope(
            "event-4",
            "run.completed",
            1,
            Instant.parse("2026-02-07T12:05:00Z"),
            created.runId(),
            "{\"status\":\"partial\",\"reason\":\"quota-reached\",\"persistedResults\":2,\"relevantCount\":1}"
        );

        runEventsConsumer.handleEvent(event);

        RunRecord updated = runRepository.findById(created.runId()).orElseThrow();
        assertThat(updated.status()).isEqualTo("partial");
        assertThat(updated.statusReason()).isEqualTo("quota-reached");

        RunSummary summary = reportService.getLatestRunSummary().orElseThrow();
        assertThat(summary.getRunId()).isEqualTo(created.runId());
        assertThat(summary.getStatus()).isEqualTo("partial");
        assertThat(summary.getDurationMs()).isEqualTo(300000L);
        assertThat(summary.getNewJobsCount()).isEqualTo(2);
        assertThat(summary.getRelevantCount()).isEqualTo(1);
    }

    @Test
    void persistsZeroResultLogsLinkedToRunId() {
        RunRecord created = runRepository.createRun("run-4", Instant.parse("2026-02-07T13:00:00Z"));
        RunEventEnvelope event = new RunEventEnvelope(
            "event-5",
            "run.completed",
            1,
            Instant.parse("2026-02-07T13:02:00Z"),
            created.runId(),
            """
                {
                  "status":"completed",
                  "newJobsCount":0,
                  "relevantCount":0,
                  "zeroResults":[
                    {
                      "queryText":"senior AND remote",
                      "domain":"workable.com",
                      "occurredAt":"2026-02-07T13:01:00Z"
                    }
                  ]
                }
                """
        );

        runEventsConsumer.handleEvent(event);
        runEventsConsumer.handleEvent(event);

        List<ZeroResultLog> zeroResultLogs = reportService.getZeroResultLogsForRun(created.runId());
        assertThat(zeroResultLogs).hasSize(1);
        ZeroResultLog log = zeroResultLogs.get(0);
        assertThat(log.runId()).isEqualTo(created.runId());
        assertThat(log.queryText()).isEqualTo("senior AND remote");
        assertThat(log.domain()).isEqualTo("workable.com");
        assertThat(log.occurredAt()).isEqualTo(Instant.parse("2026-02-07T13:01:00Z"));
    }
}
