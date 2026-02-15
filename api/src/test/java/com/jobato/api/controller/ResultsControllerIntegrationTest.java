package com.jobato.api.controller;

import com.jobato.api.repository.ActiveRunDatabase;
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
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ResultsControllerIntegrationTest {
    @TempDir
    static Path tempDir;

    @Autowired
    MockMvc mockMvc;

    @Autowired
    ActiveRunDatabase activeRunDatabase;

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
        Files.writeString(pointer, runsDir.resolve("results-test-" + UUID.randomUUID() + ".db").toString());

        try (Connection connection = activeRunDatabase.openConnection();
             Statement statement = connection.createStatement()) {
            statement.execute("""
                CREATE TABLE IF NOT EXISTS run_items (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  run_id TEXT NOT NULL,
                  query_id TEXT,
                  query_text TEXT,
                  search_query TEXT,
                  domain TEXT,
                  title TEXT,
                  snippet TEXT,
                  raw_url TEXT,
                  final_url TEXT,
                  created_at TEXT,
                  raw_html_path TEXT,
                  visible_text TEXT,
                  cache_key TEXT,
                  cached_at TEXT,
                  last_seen_at TEXT,
                  normalized_url TEXT,
                  canonical_id INTEGER,
                  is_duplicate INTEGER,
                  is_hidden INTEGER,
                  duplicate_count INTEGER,
                  relevance_score REAL,
                  scored_at TEXT,
                  score_version TEXT
                )
                """);
        }
    }

    @Test
    void todayViewReturnsLatestRunOnlyWithStableOrdering() throws Exception {
        insertRunSummary("run-old", "2026-02-14T09:00:00Z");
        insertRunSummary("run-latest", "2026-02-14T10:00:00Z");

        insertRunItem("run-old", "Old item", "2026-02-14T09:00:00Z", false);
        int latestA = insertRunItem("run-latest", "Latest A", "2026-02-14T10:00:00Z", false);
        int latestB = insertRunItem("run-latest", "Latest B", "2026-02-14T10:00:00Z", false);

        int expectedFirstId = Math.max(latestA, latestB);
        int expectedSecondId = Math.min(latestA, latestB);

        mockMvc.perform(get("/api/results").param("view", "today"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].runId").value("run-latest"))
            .andExpect(jsonPath("$[1].runId").value("run-latest"))
            .andExpect(jsonPath("$[0].id").value(expectedFirstId))
            .andExpect(jsonPath("$[1].id").value(expectedSecondId));
    }

    @Test
    void allTimeViewReturnsCrossRunHistoryWithDeterministicOrdering() throws Exception {
        insertRunSummary("run-old", "2026-02-14T09:00:00Z");
        insertRunSummary("run-new", "2026-02-14T10:00:00Z");

        int newest = insertRunItem("run-new", "Newest", "2026-02-14T10:30:00Z", false);
        int tieA = insertRunItem("run-old", "Tie A", "2026-02-14T10:00:00Z", false);
        int tieB = insertRunItem("run-new", "Tie B", "2026-02-14T10:00:00Z", false);

        int expectedTieFirst = Math.max(tieA, tieB);
        int expectedTieSecond = Math.min(tieA, tieB);

        mockMvc.perform(get("/api/results").param("view", "all-time"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].id").value(newest))
            .andExpect(jsonPath("$[1].id").value(expectedTieFirst))
            .andExpect(jsonPath("$[2].id").value(expectedTieSecond));
    }

    @Test
    void includeHiddenIsConsistentAcrossViews() throws Exception {
        insertRunSummary("run-old", "2026-02-14T09:00:00Z");
        insertRunSummary("run-latest", "2026-02-14T10:00:00Z");

        insertRunItem("run-old", "Old visible", "2026-02-14T09:30:00Z", false);
        insertRunItem("run-old", "Old hidden", "2026-02-14T09:29:00Z", true);
        insertRunItem("run-latest", "Latest visible", "2026-02-14T10:30:00Z", false);
        insertRunItem("run-latest", "Latest hidden", "2026-02-14T10:29:00Z", true);

        mockMvc.perform(get("/api/results").param("view", "today"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(1));

        mockMvc.perform(get("/api/results").param("view", "today").param("includeHidden", "true"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2));

        mockMvc.perform(get("/api/results").param("view", "all-time"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2));

        mockMvc.perform(get("/api/results").param("view", "all-time").param("includeHidden", "true"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(4));
    }

    @Test
    void runIdOverridesViewAndResponseUsesCamelCase() throws Exception {
        insertRunSummary("run-latest", "2026-02-14T11:00:00Z");
        insertRunItem("run-latest", "Latest item", "2026-02-14T11:00:00Z", false);
        insertRunItem("run-legacy", "Legacy item", "2026-02-14T10:00:00Z", false);

        mockMvc.perform(get("/api/results").param("runId", "run-legacy").param("view", "today"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].runId").value("run-legacy"))
            .andExpect(jsonPath("$[0].queryId").value("query-1"))
            .andExpect(jsonPath("$[0].run_id").doesNotExist())
            .andExpect(jsonPath("$[0].query_id").doesNotExist());
    }

    private void insertRunSummary(String runId, String triggerTime) throws Exception {
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement("""
                 INSERT INTO run_summaries (run_id, trigger_time, duration_ms, new_jobs_count, relevant_count, status)
                 VALUES (?, ?, 1000, 1, 0, 'completed')
                 """)) {
            statement.setString(1, runId);
            statement.setString(2, triggerTime);
            statement.executeUpdate();
        }
    }

    private int insertRunItem(String runId, String title, String createdAt, boolean isHidden) throws Exception {
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement("""
                 INSERT INTO run_items (
                   run_id, query_id, query_text, search_query, domain, title, snippet,
                   raw_url, final_url, created_at, raw_html_path, visible_text,
                   cache_key, cached_at, last_seen_at, normalized_url,
                   canonical_id, is_duplicate, is_hidden, duplicate_count,
                   relevance_score, scored_at, score_version
                 ) VALUES (?, 'query-1', 'Query text', 'search terms', 'example.com', ?, 'Snippet',
                           'https://example.com/raw', 'https://example.com/final', ?, null, null,
                           ?, null, null, 'norm',
                           null, 0, ?, 0,
                           0.5, ?, 'baseline')
                 """, Statement.RETURN_GENERATED_KEYS)) {
            statement.setString(1, runId);
            statement.setString(2, title);
            statement.setString(3, createdAt);
            statement.setString(4, runId + "-" + title);
            statement.setInt(5, isHidden ? 1 : 0);
            statement.setString(6, createdAt);
            statement.executeUpdate();
            try (var generatedKeys = statement.getGeneratedKeys()) {
                generatedKeys.next();
                return generatedKeys.getInt(1);
            }
        }
    }
}
