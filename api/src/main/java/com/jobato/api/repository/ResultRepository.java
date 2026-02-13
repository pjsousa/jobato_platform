package com.jobato.api.repository;

import com.jobato.api.model.ResultItem;
import org.springframework.stereotype.Repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Repository
public class ResultRepository {
    private final ActiveRunDatabase activeRunDatabase;

    public ResultRepository(ActiveRunDatabase activeRunDatabase) {
        this.activeRunDatabase = activeRunDatabase;
    }

    public List<ResultItem> findByRunId(String runId, boolean includeHidden) {
        StringBuilder sql = new StringBuilder("""
            SELECT id, run_id, query_id, query_text, search_query, domain, title, snippet,
                   raw_url, final_url, created_at, raw_html_path, visible_text,
                   cache_key, cached_at, last_seen_at, normalized_url,
                   canonical_id, is_duplicate, is_hidden, duplicate_count,
                   relevance_score, scored_at, score_version
            FROM run_items
            WHERE run_id = ?
            """);
        
        if (!includeHidden) {
            sql.append(" AND (is_hidden = 0 OR is_hidden IS NULL)");
        }
        
        sql.append(" ORDER BY created_at DESC");
        
        List<ResultItem> results = new ArrayList<>();
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql.toString())) {
            statement.setString(1, runId);
            ResultSet resultSet = statement.executeQuery();
            while (resultSet.next()) {
                results.add(map(resultSet));
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load results for run: " + runId, exception);
        }
        return results;
    }

    public Optional<ResultItem> findById(Integer id) {
        String sql = """
            SELECT id, run_id, query_id, query_text, search_query, domain, title, snippet,
                   raw_url, final_url, created_at, raw_html_path, visible_text,
                   cache_key, cached_at, last_seen_at, normalized_url,
                   canonical_id, is_duplicate, is_hidden, duplicate_count,
                   relevance_score, scored_at, score_version
            FROM run_items
            WHERE id = ?
            """;
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setInt(1, id);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return Optional.of(map(resultSet));
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load result by id: " + id, exception);
        }
        return Optional.empty();
    }

    public List<ResultItem> findByRunIdAndQueryId(String runId, String queryId, boolean includeHidden) {
        StringBuilder sql = new StringBuilder("""
            SELECT id, run_id, query_id, query_text, search_query, domain, title, snippet,
                   raw_url, final_url, created_at, raw_html_path, visible_text,
                   cache_key, cached_at, last_seen_at, normalized_url,
                   canonical_id, is_duplicate, is_hidden, duplicate_count,
                   relevance_score, scored_at, score_version
            FROM run_items
            WHERE run_id = ? AND query_id = ?
            """);
        
        if (!includeHidden) {
            sql.append(" AND (is_hidden = 0 OR is_hidden IS NULL)");
        }
        
        sql.append(" ORDER BY created_at DESC");
        
        List<ResultItem> results = new ArrayList<>();
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql.toString())) {
            statement.setString(1, runId);
            statement.setString(2, queryId);
            ResultSet resultSet = statement.executeQuery();
            while (resultSet.next()) {
                results.add(map(resultSet));
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load results for run and query", exception);
        }
        return results;
    }

    public List<ResultItem> findAllForRun(String runId) {
        return findByRunId(runId, true);
    }

    public List<ResultItem> findVisibleForRun(String runId) {
        return findByRunId(runId, false);
    }

    public int countByRunId(String runId, boolean includeHidden) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM run_items WHERE run_id = ?");
        
        if (!includeHidden) {
            sql.append(" AND (is_hidden = 0 OR is_hidden IS NULL)");
        }
        
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql.toString())) {
            statement.setString(1, runId);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return resultSet.getInt(1);
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to count results for run: " + runId, exception);
        }
        return 0;
    }

    public int countDuplicatesForRun(String runId) {
        String sql = "SELECT COUNT(*) FROM run_items WHERE run_id = ? AND is_duplicate = 1";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, runId);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return resultSet.getInt(1);
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to count duplicates for run: " + runId, exception);
        }
        return 0;
    }

    private ResultItem map(ResultSet resultSet) throws SQLException {
        Integer id = resultSet.getInt("id");
        String runId = resultSet.getString("run_id");
        String queryId = resultSet.getString("query_id");
        String queryText = resultSet.getString("query_text");
        String searchQuery = resultSet.getString("search_query");
        String domain = resultSet.getString("domain");
        String title = resultSet.getString("title");
        String snippet = resultSet.getString("snippet");
        String rawUrl = resultSet.getString("raw_url");
        String finalUrl = resultSet.getString("final_url");
        String createdAt = resultSet.getString("created_at");
        String rawHtmlPath = resultSet.getString("raw_html_path");
        String visibleText = resultSet.getString("visible_text");
        String cacheKey = resultSet.getString("cache_key");
        String cachedAt = resultSet.getString("cached_at");
        String lastSeenAt = resultSet.getString("last_seen_at");
        String normalizedUrl = resultSet.getString("normalized_url");
        
        // Dedupe fields - handle nulls
        Integer canonicalId = resultSet.getObject("canonical_id") != null ?
            resultSet.getInt("canonical_id") : null;
        Boolean isDuplicate = resultSet.getObject("is_duplicate") != null ?
            resultSet.getInt("is_duplicate") == 1 : false;
        Boolean isHidden = resultSet.getObject("is_hidden") != null ?
            resultSet.getInt("is_hidden") == 1 : false;
        Integer duplicateCount = resultSet.getObject("duplicate_count") != null ?
            resultSet.getInt("duplicate_count") : 0;

        // Scoring fields - handle nulls
        Double relevanceScore = resultSet.getObject("relevance_score") != null ?
            resultSet.getDouble("relevance_score") : null;
        String scoredAt = resultSet.getString("scored_at");
        String scoreVersion = resultSet.getString("score_version");

        return new ResultItem(
            id, runId, queryId, queryText, searchQuery, domain, title, snippet,
            rawUrl, finalUrl, createdAt, rawHtmlPath, visibleText,
            cacheKey, cachedAt, lastSeenAt, normalizedUrl,
            canonicalId, isDuplicate, isHidden, duplicateCount,
            relevanceScore, scoredAt, scoreVersion
        );
    }
}
