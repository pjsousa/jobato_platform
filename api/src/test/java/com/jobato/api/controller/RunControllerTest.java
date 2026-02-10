package com.jobato.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.jobato.api.dto.RunResponse;
import com.jobato.api.messaging.RunEventPublisher;
import com.jobato.api.model.AllowlistEntry;
import com.jobato.api.model.QueryDefinition;
import com.jobato.api.model.RunRecord;
import com.jobato.api.repository.AllowlistRepository;
import com.jobato.api.repository.QueryRepository;
import com.jobato.api.repository.RunRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.time.LocalDate;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.nullValue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RunControllerTest {
    @TempDir
    static Path tempDir;

    @Autowired
    MockMvc mockMvc;

    @Autowired
    QueryRepository queryRepository;

    @Autowired
    AllowlistRepository allowlistRepository;

    @Autowired
    RunRepository runRepository;

    @Autowired
    ObjectMapper objectMapper;

    @MockitoBean
    RunEventPublisher runEventPublisher;

    @DynamicPropertySource
    static void registerProperties(DynamicPropertyRegistry registry) {
        registry.add("CONFIG_DIR", () -> tempDir.resolve("config").toString());
        registry.add("quota.file-path", () -> tempDir.resolve("config/quota.yaml").toString());
        registry.add("allowlist.file-path", () -> tempDir.resolve("config/allowlists.yaml").toString());
        registry.add("DATA_DIR", () -> tempDir.resolve("data").toString());
        registry.add("jobato.redis.streams.enabled", () -> "false");
    }

    @BeforeEach
    void setup() throws Exception {
        Path configDir = tempDir.resolve("config");
        Files.createDirectories(configDir);
        Path dataDir = tempDir.resolve("data/db/runs");
        Files.createDirectories(dataDir);
        Path pointer = tempDir.resolve("data/db/current-db.txt");
        Files.createDirectories(pointer.getParent());
        Files.writeString(pointer, dataDir.resolve("runs-" + UUID.randomUUID() + ".db").toString());

        Path quotaConfig = configDir.resolve("quota.yaml");
        Files.writeString(quotaConfig, """
            {
              \"quota\": {
                \"dailyLimit\": 1,
                \"concurrencyLimit\": 1,
                \"resetPolicy\": {
                  \"timeZone\": \"UTC\",
                  \"resetHour\": 0
                }
              }
            }
            """);

        Path quotaDb = tempDir.resolve("data/db/quota/quota.db");
        Files.createDirectories(quotaDb.getParent());
        Files.deleteIfExists(quotaDb);

        queryRepository.saveAll(List.of(
            new QueryDefinition("q-1", "Data Analyst", true, "2026-02-07T10:00:00Z", "2026-02-07T10:00:00Z")
        ));
        allowlistRepository.saveAll(List.of(
            new AllowlistEntry("example.com", true)
        ));
    }

    @Test
    void createsRunAndPublishesEvent() throws Exception {
        MvcResult result = mockMvc.perform(post("/api/runs"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.runId").isNotEmpty())
            .andExpect(jsonPath("$.status").value("running"))
            .andReturn();

        RunResponse response = objectMapper.readValue(result.getResponse().getContentAsString(), RunResponse.class);
        assertThat(runRepository.findById(response.runId())).isPresent();

        ArgumentCaptor<String> runIdCaptor = ArgumentCaptor.forClass(String.class);
        verify(runEventPublisher).publishRunRequested(runIdCaptor.capture(), any(), any());
        assertThat(runIdCaptor.getValue()).isEqualTo(response.runId());
    }

    @Test
    void rejectsRunWhenAnotherIsInProgress() throws Exception {
        runRepository.createRun("run-1", Instant.parse("2026-02-07T10:00:00Z"));

        mockMvc.perform(post("/api/runs"))
            .andExpect(status().isConflict())
            .andExpect(jsonPath("$.errorCode").value("RUN_IN_PROGRESS"));

        verify(runEventPublisher, never()).publishRunRequested(any(), any(), any());
    }

    @Test
    void rejectsRunWhenQuotaReached() throws Exception {
        String quotaDay = LocalDate.now(ZoneOffset.UTC).toString();
        Path quotaDb = tempDir.resolve("data/db/quota/quota.db");
        seedQuotaUsage(quotaDb, quotaDay, "seed-run", 1);

        mockMvc.perform(post("/api/runs"))
            .andExpect(status().isTooManyRequests())
            .andExpect(jsonPath("$.errorCode").value("QUOTA_REACHED"));

        verify(runEventPublisher, never()).publishRunRequested(any(), any(), any());
    }

    @Test
    void returnsRunStatusById() throws Exception {
        RunRecord created = runRepository.createRun("run-lookup", Instant.parse("2026-02-07T12:00:00Z"));

        mockMvc.perform(get("/api/runs/{id}", created.runId()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.runId").value(created.runId()))
            .andExpect(jsonPath("$.status").value("running"))
            .andExpect(jsonPath("$.startedAt").value("2026-02-07T12:00:00Z"))
            .andExpect(jsonPath("$.endedAt").value(nullValue()));
    }

    private void seedQuotaUsage(Path quotaDb, String day, String runId, int count) throws Exception {
        try (Connection connection = DriverManager.getConnection("jdbc:sqlite:" + quotaDb.toAbsolutePath())) {
            try (PreparedStatement create = connection.prepareStatement(
                "CREATE TABLE IF NOT EXISTS quota_usage (day TEXT, run_id TEXT, count INTEGER, PRIMARY KEY(day, run_id))"
            )) {
                create.executeUpdate();
            }
            try (PreparedStatement insert = connection.prepareStatement(
                "INSERT INTO quota_usage (day, run_id, count) VALUES (?, ?, ?)"
            )) {
                insert.setString(1, day);
                insert.setString(2, runId);
                insert.setInt(3, count);
                insert.executeUpdate();
            }
        }
    }
}
