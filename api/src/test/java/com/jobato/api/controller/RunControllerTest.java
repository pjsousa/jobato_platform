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
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
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

    @MockBean
    RunEventPublisher runEventPublisher;

    @DynamicPropertySource
    static void registerProperties(DynamicPropertyRegistry registry) {
        registry.add("CONFIG_DIR", () -> tempDir.resolve("config").toString());
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
    void returnsRunStatusById() throws Exception {
        RunRecord created = runRepository.createRun("run-lookup", Instant.parse("2026-02-07T12:00:00Z"));

        mockMvc.perform(get("/api/runs/{id}", created.runId()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.runId").value(created.runId()))
            .andExpect(jsonPath("$.status").value("running"))
            .andExpect(jsonPath("$.startedAt").value("2026-02-07T12:00:00Z"))
            .andExpect(jsonPath("$.endedAt").value(nullValue()));
    }
}
