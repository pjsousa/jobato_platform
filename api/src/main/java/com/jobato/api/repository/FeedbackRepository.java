package com.jobato.api.repository;

import com.jobato.api.model.ManualFeedback;
import org.springframework.stereotype.Repository;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Optional;

@Repository
public class FeedbackRepository {
    private final ActiveRunDatabase activeRunDatabase;

    public FeedbackRepository(ActiveRunDatabase activeRunDatabase) {
        this.activeRunDatabase = activeRunDatabase;
    }

    public void upsert(String identityKey, String manualLabel, String updatedAt) {
        String sql = """
            INSERT INTO manual_feedback (identity_key, manual_label, manual_label_updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(identity_key) DO UPDATE SET
              manual_label = excluded.manual_label,
              manual_label_updated_at = excluded.manual_label_updated_at
            """;

        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, identityKey);
            statement.setString(2, manualLabel);
            statement.setString(3, updatedAt);
            statement.executeUpdate();
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to save manual feedback", exception);
        }
    }

    public Optional<ManualFeedback> findByIdentityKey(String identityKey) {
        String sql = """
            SELECT manual_label, manual_label_updated_at
            FROM manual_feedback
            WHERE identity_key = ?
            """;
        try (Connection connection = activeRunDatabase.openConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, identityKey);
            ResultSet resultSet = statement.executeQuery();
            if (resultSet.next()) {
                return Optional.of(new ManualFeedback(
                    resultSet.getString("manual_label"),
                    resultSet.getString("manual_label_updated_at")
                ));
            }
        } catch (SQLException exception) {
            throw new IllegalStateException("Failed to read manual feedback", exception);
        }
        return Optional.empty();
    }
}
