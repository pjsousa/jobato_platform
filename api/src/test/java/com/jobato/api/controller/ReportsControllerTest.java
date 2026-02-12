package com.jobato.api.controller;

import com.jobato.api.service.ReportService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ReportsControllerTest {
    @TempDir
    static Path tempDir;

    @Autowired
    MockMvc mockMvc;

    @Autowired
    ReportService reportService;

    @DynamicPropertySource
    static void registerProperties(DynamicPropertyRegistry registry) {
        registry.add("DATA_DIR", () -> tempDir.resolve("data").toString());
        registry.add("jobato.redis.streams.enabled", () -> "false");
    }

    @BeforeEach
    void setup() throws Exception {
        Path dataDir = tempDir.resolve("data");
        Path runsDir = dataDir.resolve("db/runs");
        Files.createDirectories(runsDir);

        Path pointer = dataDir.resolve("db/current-db.txt");
        Files.createDirectories(pointer.getParent());
        Files.writeString(pointer, runsDir.resolve("reports-test-" + UUID.randomUUID() + ".db").toString());
    }

    @Test
    void returnsNoContentWhenNoSummaryExists() throws Exception {
        mockMvc.perform(get("/api/reports/runs/latest"))
            .andExpect(status().isNoContent());
    }

    @Test
    void returnsLatestRunSummaryWithCamelCaseFields() throws Exception {
        reportService.saveRunSummary(
            "run-abc",
            Instant.parse("2026-02-12T10:00:00Z"),
            123456L,
            8,
            0,
            "completed"
        );

        mockMvc.perform(get("/api/reports/runs/latest"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.runId").value("run-abc"))
            .andExpect(jsonPath("$.status").value("completed"))
            .andExpect(jsonPath("$.triggerTime").value("2026-02-12T10:00:00Z"))
            .andExpect(jsonPath("$.durationMs").value(123456))
            .andExpect(jsonPath("$.newJobsCount").value(8))
            .andExpect(jsonPath("$.relevantCount").value(0));
    }
}
