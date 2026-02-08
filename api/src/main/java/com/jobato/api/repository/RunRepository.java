package com.jobato.api.repository;

import com.jobato.api.model.RunRecord;
import org.springframework.stereotype.Repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.Optional;

@Repository
public class RunRepository {
    private static final String STATUS_RUNNING = "running";

    private final ActiveRunDatabase activeRunDatabase;

    public RunRepository(ActiveRunDatabase activeRunDatabase) {
        this.activeRunDatabase = activeRunDatabase;
    }

    public Optional<RunRecord> findActiveRun() {
        String sql = "SELECT run_id, status, started_at, ended_at FROM runs WHERE status = ? ORDER BY started_at DESC LIMIT 1";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, STATUS_RUNNING);
            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    return Optional.of(map(resultSet));
                }
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load active run", exception);
        }
        return Optional.empty();
    }

    public RunRecord createRun(String runId, Instant startedAt) {
        String sql = "INSERT INTO runs (run_id, status, started_at) VALUES (?, ?, ?)";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, runId);
            statement.setString(2, STATUS_RUNNING);
            statement.setString(3, startedAt.toString());
            statement.executeUpdate();
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to create run", exception);
        }
        return new RunRecord(runId, STATUS_RUNNING, startedAt, null);
    }

    public Optional<RunRecord> findById(String runId) {
        String sql = "SELECT run_id, status, started_at, ended_at FROM runs WHERE run_id = ?";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, runId);
            try (ResultSet resultSet = statement.executeQuery()) {
                if (resultSet.next()) {
                    return Optional.of(map(resultSet));
                }
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to load run", exception);
        }
        return Optional.empty();
    }

    public boolean updateRunStatusIfRunning(String runId, String status, Instant endedAt) {
        String sql = "UPDATE runs SET status = ?, ended_at = ? WHERE run_id = ? AND status = ? AND ended_at IS NULL";
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, status);
            statement.setString(2, endedAt.toString());
            statement.setString(3, runId);
            statement.setString(4, STATUS_RUNNING);
            return statement.executeUpdate() > 0;
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to update run status", exception);
        }
    }

    private RunRecord map(ResultSet resultSet) throws SQLException {
        String runId = resultSet.getString("run_id");
        String status = resultSet.getString("status");
        Instant startedAt = Instant.parse(resultSet.getString("started_at"));
        String endedAtValue = resultSet.getString("ended_at");
        Instant endedAt = endedAtValue == null ? null : Instant.parse(endedAtValue);
        return new RunRecord(runId, status, startedAt, endedAt);
    }
}
