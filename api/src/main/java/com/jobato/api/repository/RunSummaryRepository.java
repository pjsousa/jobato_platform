package com.jobato.api.repository;

import com.jobato.api.model.RunSummary;
import org.springframework.stereotype.Repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.Optional;

@Repository
public class RunSummaryRepository {
    private final ActiveRunDatabase activeRunDatabase;

    public RunSummaryRepository(ActiveRunDatabase activeRunDatabase) {
        this.activeRunDatabase = activeRunDatabase;
    }

    public void save(RunSummary runSummary) {
        String sql = "INSERT INTO run_summaries (run_id, trigger_time, duration_ms, new_jobs_count, relevant_count, status) VALUES (?, ?, ?, ?, ?, ?)";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, runSummary.getRunId());
            statement.setString(2, runSummary.getTriggerTime().toString());
            statement.setLong(3, runSummary.getDurationMs());
            statement.setInt(4, runSummary.getNewJobsCount());
            statement.setInt(5, runSummary.getRelevantCount());
            statement.setString(6, runSummary.getStatus());
            statement.executeUpdate();
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to save run summary", exception);
        }
    }

    public Optional<RunSummary> findLatest() {
        String sql = "SELECT run_id, trigger_time, duration_ms, new_jobs_count, relevant_count, status FROM run_summaries ORDER BY trigger_time DESC LIMIT 1";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql);
             ResultSet resultSet = statement.executeQuery()) {
            if (resultSet.next()) {
                return Optional.of(map(resultSet));
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load latest run summary", exception);
        }
        return Optional.empty();
    }

    private RunSummary map(ResultSet resultSet) throws SQLException {
        String runId = resultSet.getString("run_id");
        Instant triggerTime = Instant.parse(resultSet.getString("trigger_time"));
        Long durationMs = resultSet.getLong("duration_ms");
        Integer newJobsCount = resultSet.getInt("new_jobs_count");
        Integer relevantCount = resultSet.getInt("relevant_count");
        String status = resultSet.getString("status");
        return new RunSummary(runId, triggerTime, durationMs, newJobsCount, relevantCount, status);
    }
}