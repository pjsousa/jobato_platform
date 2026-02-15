package com.jobato.api.repository;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class ActiveRunDatabase {
    private static final String DEFAULT_DB_FILE = "db/runs/active.db";
    private static final String CREATE_RUNS_TABLE = """
        CREATE TABLE IF NOT EXISTS runs (
          run_id TEXT PRIMARY KEY,
          status TEXT NOT NULL,
          started_at TEXT NOT NULL,
          ended_at TEXT,
          status_reason TEXT
        )
        """;
    private static final String CREATE_RUN_SUMMARIES_TABLE = """
        CREATE TABLE IF NOT EXISTS run_summaries (
          run_id TEXT PRIMARY KEY,
          trigger_time TEXT NOT NULL,
          duration_ms INTEGER NOT NULL,
          new_jobs_count INTEGER NOT NULL,
          relevant_count INTEGER NOT NULL,
          status TEXT NOT NULL
        )
        """;
    private static final String CREATE_ZERO_RESULT_LOGS_TABLE = """
        CREATE TABLE IF NOT EXISTS zero_result_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id TEXT NOT NULL,
          query_text TEXT NOT NULL,
          domain TEXT NOT NULL,
          occurred_at TEXT NOT NULL,
          UNIQUE(run_id, query_text, domain)
        )
        """;
    private static final String CREATE_MANUAL_FEEDBACK_TABLE = """
        CREATE TABLE IF NOT EXISTS manual_feedback (
          identity_key TEXT PRIMARY KEY,
          manual_label TEXT,
          manual_label_updated_at TEXT NOT NULL
        )
        """;
    private static final String STATUS_REASON_COLUMN = "status_reason";
    private static final String ADD_STATUS_REASON_COLUMN = "ALTER TABLE runs ADD COLUMN status_reason TEXT";
    private static final String CREATE_STATUS_INDEX =
        "CREATE INDEX IF NOT EXISTS idx_runs__status ON runs(status)";
    private static final String CREATE_ZERO_RESULT_LOGS_RUN_ID_INDEX =
        "CREATE INDEX IF NOT EXISTS idx_zero_result_logs__run_id ON zero_result_logs(run_id)";

    private final Path dataDir;
    private final Set<Path> initializedPaths = ConcurrentHashMap.newKeySet();
    private final Object schemaLock = new Object();

    public ActiveRunDatabase(@Value("${DATA_DIR:data}") String dataDir) {
        this.dataDir = Path.of(dataDir);
    }

    public Connection openConnection() {
        Path dbPath = resolveActiveDbPath();
        try {
            Connection connection = DriverManager.getConnection("jdbc:sqlite:" + dbPath.toAbsolutePath());
            ensureSchema(connection, dbPath);
            return connection;
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to connect to runs database", exception);
        }
    }

    private Path resolveActiveDbPath() {
        Path pointerPath = dataDir.resolve("db/current-db.txt");
        String pointerValue = "";
        if (Files.exists(pointerPath)) {
            try {
                pointerValue = Files.readString(pointerPath, StandardCharsets.UTF_8).trim();
            } catch (IOException exception) {
                throw new UncheckedIOException("Failed to read current-db.txt", exception);
            }
        }

        Path dbPath;
        if (pointerValue.isBlank()) {
            dbPath = dataDir.resolve(DEFAULT_DB_FILE);
        } else {
            Path resolved = Path.of(pointerValue);
            dbPath = resolved.isAbsolute() ? resolved : dataDir.resolve(resolved);
        }

        try {
            Path parent = dbPath.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
        } catch (IOException exception) {
            throw new UncheckedIOException("Failed to prepare runs database directory", exception);
        }

        return dbPath;
    }

    private void ensureSchema(Connection connection, Path dbPath) {
        if (initializedPaths.contains(dbPath)) {
            return;
        }
        synchronized (schemaLock) {
            if (initializedPaths.contains(dbPath)) {
                return;
            }
            try (Statement statement = connection.createStatement()) {
                statement.execute(CREATE_RUNS_TABLE);
                statement.execute(CREATE_RUN_SUMMARIES_TABLE);
                statement.execute(CREATE_ZERO_RESULT_LOGS_TABLE);
                statement.execute(CREATE_MANUAL_FEEDBACK_TABLE);
                statement.execute(CREATE_STATUS_INDEX);
                statement.execute(CREATE_ZERO_RESULT_LOGS_RUN_ID_INDEX);
                if (!columnExists(connection, "runs", STATUS_REASON_COLUMN)) {
                    statement.execute(ADD_STATUS_REASON_COLUMN);
                }
            } catch (SQLException exception) {
                throw new IllegalStateException("Failed to initialize runs schema", exception);
            }
            initializedPaths.add(dbPath);
        }
    }

    private boolean columnExists(Connection connection, String tableName, String columnName) throws SQLException {
        try (Statement statement = connection.createStatement();
             ResultSet resultSet = statement.executeQuery("PRAGMA table_info(" + tableName + ")")) {
            while (resultSet.next()) {
                String name = resultSet.getString("name");
                if (columnName.equalsIgnoreCase(name)) {
                    return true;
                }
            }
        }
        return false;
    }
}
