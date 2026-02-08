package com.jobato.api.repository;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

@Repository
public class QuotaUsageRepository {
    private static final String QUOTA_TABLE = "quota_usage";
    private final Path dataDir;

    public QuotaUsageRepository(@Value("${DATA_DIR:data}") String dataDir) {
        this.dataDir = Path.of(dataDir);
    }

    public int getDailyUsage(String day) {
        Path dbPath = resolveQuotaDbPath();
        if (!Files.exists(dbPath)) {
            return 0;
        }

        try (Connection connection = DriverManager.getConnection("jdbc:sqlite:" + dbPath.toAbsolutePath())) {
            if (!quotaTableExists(connection)) {
                return 0;
            }
            String sql = "SELECT SUM(count) AS total FROM quota_usage WHERE day = ?";
            try (PreparedStatement statement = connection.prepareStatement(sql)) {
                statement.setString(1, day);
                try (ResultSet resultSet = statement.executeQuery()) {
                    if (resultSet.next()) {
                        return resultSet.getInt("total");
                    }
                }
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to read quota usage", exception);
        }

        return 0;
    }

    private boolean quotaTableExists(Connection connection) throws SQLException {
        String sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='" + QUOTA_TABLE + "'";
        try (PreparedStatement statement = connection.prepareStatement(sql);
             ResultSet resultSet = statement.executeQuery()) {
            return resultSet.next();
        }
    }

    private Path resolveQuotaDbPath() {
        return dataDir.resolve("db/quota/quota.db");
    }
}
