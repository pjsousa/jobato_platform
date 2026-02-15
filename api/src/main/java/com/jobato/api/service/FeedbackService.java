package com.jobato.api.service;

import com.jobato.api.model.FeedbackLabel;
import com.jobato.api.model.ManualFeedback;
import com.jobato.api.model.ResultItem;
import com.jobato.api.repository.FeedbackRepository;
import com.jobato.api.repository.ResultRepository;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

@Service
public class FeedbackService {
    private final ResultRepository resultRepository;
    private final FeedbackRepository feedbackRepository;
    private final Clock clock;

    public FeedbackService(ResultRepository resultRepository, FeedbackRepository feedbackRepository, Clock clock) {
        this.resultRepository = resultRepository;
        this.feedbackRepository = feedbackRepository;
        this.clock = clock;
    }

    public ManualFeedback setManualLabel(Integer resultId, String labelValue) {
        ResultItem result = resultRepository.findById(resultId)
            .orElseThrow(() -> new FeedbackNotFoundException("Result not found: " + resultId));

        FeedbackLabel label;
        try {
            label = FeedbackLabel.fromApiValue(labelValue);
        } catch (IllegalArgumentException exception) {
            throw new FeedbackValidationException(exception.getMessage());
        }

        String timestamp = Instant.now(clock).toString();
        String persistedLabel = label != null ? label.getApiValue() : null;

        for (String identityKey : resolveIdentityKeys(result)) {
            feedbackRepository.upsert(identityKey, persistedLabel, timestamp);
        }

        return new ManualFeedback(persistedLabel, timestamp);
    }

    public ManualFeedback resolveManualFeedback(ResultItem result) {
        for (String identityKey : resolveIdentityKeys(result)) {
            Optional<ManualFeedback> feedback = feedbackRepository.findByIdentityKey(identityKey);
            if (feedback.isPresent()) {
                return feedback.get();
            }
        }

        return new ManualFeedback(null, null);
    }

    private List<String> resolveIdentityKeys(ResultItem result) {
        LinkedHashSet<String> keys = new LinkedHashSet<>();

        Integer canonicalId = result.getCanonicalId() != null ? result.getCanonicalId() : result.getId();
        if (canonicalId != null) {
            keys.add("canonical:" + canonicalId);
        }

        String normalizedUrl = normalizeUrl(result.getNormalizedUrl());
        if (normalizedUrl != null) {
            keys.add("url:" + normalizedUrl);
        }

        if (keys.isEmpty()) {
            throw new FeedbackValidationException("Result is missing identity fields required for feedback persistence");
        }

        return new ArrayList<>(keys);
    }

    private String normalizeUrl(String value) {
        if (value == null) {
            return null;
        }

        String normalized = value.trim().toLowerCase(Locale.ROOT);
        return normalized.isBlank() ? null : normalized;
    }
}
