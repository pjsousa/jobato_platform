package com.jobato.api.repository;

import com.jobato.api.model.ResultItem;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;

class ResultRepositoryOrderingTest {
    @TempDir
    Path tempDir;

    private ResultRepository repository;
    private ActiveRunDatabase activeRunDatabase;

    @BeforeEach
    void setUp() throws Exception {
        Path dataDir = tempDir.resolve("data");
        Path runsDir = dataDir.resolve("db/runs");
        Files.createDirectories(runsDir);

        Path pointer = dataDir.resolve("db/current-db.txt");
        Files.createDirectories(pointer.getParent());
        Files.writeString(pointer, runsDir.resolve("results-ordering-" + UUID.randomUUID() + ".db").toString());

        activeRunDatabase = new ActiveRunDatabase(dataDir.toString());
        repository = new ResultRepository(activeRunDatabase);

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
    void findByRunId_ordersByCreatedAtDescThenIdDescWhenTimestampsTie() throws Exception {
        int older = insertRunItem("run-1", "query-1", "Older", "2026-02-14T09:00:00Z", false);
        int tieA = insertRunItem("run-1", "query-1", "Tie A", "2026-02-14T10:00:00Z", false);
        int tieB = insertRunItem("run-1", "query-1", "Tie B", "2026-02-14T10:00:00Z", false);
        int newest = insertRunItem("run-1", "query-1", "Newest", "2026-02-14T11:00:00Z", false);

        List<ResultItem> results = repository.findByRunId("run-1", false);

        assertEquals(List.of(newest, Math.max(tieA, tieB), Math.min(tieA, tieB), older),
            results.stream().map(ResultItem::getId).toList());
    }

    @Test
    void findByRunIdAndQueryId_appliesSameDeterministicOrderAndIncludeHiddenPolicy() throws Exception {
        int visibleOld = insertRunItem("run-2", "query-7", "Visible old", "2026-02-14T09:00:00Z", false);
        int hiddenTie = insertRunItem("run-2", "query-7", "Hidden tie", "2026-02-14T10:00:00Z", true);
        int visibleTie = insertRunItem("run-2", "query-7", "Visible tie", "2026-02-14T10:00:00Z", false);
        insertRunItem("run-2", "query-other", "Different query", "2026-02-14T12:00:00Z", false);

        List<ResultItem> visibleOnly = repository.findByRunIdAndQueryId("run-2", "query-7", false);
        List<ResultItem> includingHidden = repository.findByRunIdAndQueryId("run-2", "query-7", true);

        assertEquals(List.of(Math.max(visibleTie, hiddenTie), Math.min(visibleTie, hiddenTie), visibleOld),
            includingHidden.stream().map(ResultItem::getId).toList());
        assertEquals(List.of(visibleTie, visibleOld), visibleOnly.stream().map(ResultItem::getId).toList());
    }

    private int insertRunItem(String runId, String queryId, String title, String createdAt, boolean isHidden) throws Exception {
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement("""
                 INSERT INTO run_items (
                   run_id, query_id, query_text, search_query, domain, title, snippet,
                   raw_url, final_url, created_at, raw_html_path, visible_text,
                   cache_key, cached_at, last_seen_at, normalized_url,
                   canonical_id, is_duplicate, is_hidden, duplicate_count,
                   relevance_score, scored_at, score_version
                 ) VALUES (?, ?, 'Query text', 'search terms', 'example.com', ?, 'Snippet',
                           'https://example.com/raw', 'https://example.com/final', ?, null, null,
                           ?, null, null, 'norm',
                           null, 0, ?, 0,
                           0.5, ?, 'baseline')
                 """, Statement.RETURN_GENERATED_KEYS)) {
            statement.setString(1, runId);
            statement.setString(2, queryId);
            statement.setString(3, title);
            statement.setString(4, createdAt);
            statement.setString(5, runId + "-" + queryId + "-" + title);
            statement.setInt(6, isHidden ? 1 : 0);
            statement.setString(7, createdAt);
            statement.executeUpdate();

            try (var keys = statement.getGeneratedKeys()) {
                keys.next();
                return keys.getInt(1);
            }
        }
    }
}
