package com.jobato.api.controller;

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

import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class AllowlistControllerTest {
    @TempDir
    static Path tempDir;

    @Autowired
    MockMvc mockMvc;

    @DynamicPropertySource
    static void registerProperties(DynamicPropertyRegistry registry) {
        registry.add("allowlist.file-path", () -> tempDir.resolve("allowlists.yaml").toString());
    }

    @BeforeEach
    void clearAllowlistFile() throws Exception {
        Files.deleteIfExists(tempDir.resolve("allowlists.yaml"));
    }

    @Test
    void listReturnsEmptyArrayWhenNoEntries() throws Exception {
        mockMvc.perform(get("/api/allowlists"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$").isEmpty());
    }

    @Test
    void createReturnsCreatedEntry() throws Exception {
        mockMvc.perform(post("/api/allowlists")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"example.com\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.domain").value("example.com"))
                .andExpect(jsonPath("$.enabled").value(true));
    }

    @Test
    void createRejectsDuplicateDomains() throws Exception {
        mockMvc.perform(post("/api/allowlists")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"example.com\"}"))
                .andExpect(status().isCreated());

        mockMvc.perform(post("/api/allowlists")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"example.com\"}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.errorCode").value("allowlist.duplicateDomain"));
    }

    @Test
    void patchUpdatesEnabledFlag() throws Exception {
        mockMvc.perform(post("/api/allowlists")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"example.com\"}"))
                .andExpect(status().isCreated());

        mockMvc.perform(patch("/api/allowlists/example.com")
                        .contentType(APPLICATION_JSON)
                        .content("{\"enabled\":false}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.domain").value("example.com"))
                .andExpect(jsonPath("$.enabled").value(false));
    }

    @Test
    void patchUpdatesDomainValue() throws Exception {
        mockMvc.perform(post("/api/allowlists")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"example.com\"}"))
                .andExpect(status().isCreated());

        mockMvc.perform(patch("/api/allowlists/example.com")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"jobs.example.com\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.domain").value("jobs.example.com"));
    }

    @Test
    void createRejectsInvalidDomain() throws Exception {
        mockMvc.perform(post("/api/allowlists")
                        .contentType(APPLICATION_JSON)
                        .content("{\"domain\":\"bad_domain\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errorCode").value("allowlist.invalidDomain"));
    }
}
