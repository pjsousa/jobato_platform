package com.jobato.api.repository;

import com.jobato.api.model.ZeroResultLog;
import org.springframework.stereotype.Repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Repository
public class ZeroResultLogRepository {
    private final ActiveRunDatabase activeRunDatabase;

    public ZeroResultLogRepository(ActiveRunDatabase activeRunDatabase) {
        this.activeRunDatabase = activeRunDatabase;
    }

    public void saveAll(List<ZeroResultLog> logs) {
        if (logs == null || logs.isEmpty()) {
            return;
        }

        String sql = """
            INSERT INTO zero_result_logs (run_id, query_text, domain, occurred_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(run_id, query_text, domain)
            DO UPDATE SET occurred_at = excluded.occurred_at
            """;

        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            for (ZeroResultLog log : logs) {
                statement.setString(1, log.runId());
                statement.setString(2, log.queryText());
                statement.setString(3, log.domain());
                statement.setString(4, log.occurredAt().toString());
                statement.addBatch();
            }
            statement.executeBatch();
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to save zero-result logs", exception);
        }
    }

    public List<ZeroResultLog> findByRunId(String runId) {
        if (runId == null || runId.isBlank()) {
            return Collections.emptyList();
        }

        String sql = """
            SELECT run_id, query_text, domain, occurred_at
            FROM zero_result_logs
            WHERE run_id = ?
            ORDER BY occurred_at ASC, id ASC
            """;

        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, runId);
            try (ResultSet resultSet = statement.executeQuery()) {
                List<ZeroResultLog> logs = new ArrayList<>();
                while (resultSet.next()) {
                    logs.add(map(resultSet));
                }
                return logs;
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load zero-result logs", exception);
        }
    }

    private ZeroResultLog map(ResultSet resultSet) throws SQLException {
        String runId = resultSet.getString("run_id");
        String queryText = resultSet.getString("query_text");
        String domain = resultSet.getString("domain");
        Instant occurredAt = Instant.parse(resultSet.getString("occurred_at"));
        return new ZeroResultLog(runId, queryText, domain, occurredAt);
    }
}
