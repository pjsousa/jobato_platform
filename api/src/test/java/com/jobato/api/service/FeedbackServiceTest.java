package com.jobato.api.service;

import com.jobato.api.model.ManualFeedback;
import com.jobato.api.model.ResultItem;
import com.jobato.api.repository.FeedbackRepository;
import com.jobato.api.repository.ResultRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.ArgumentMatchers.anyString;

class FeedbackServiceTest {
    private static final Instant NOW = Instant.parse("2026-02-15T12:00:00Z");

    private ResultRepository resultRepository;
    private FeedbackRepository feedbackRepository;
    private FeedbackService feedbackService;

    @BeforeEach
    void setUp() {
        resultRepository = org.mockito.Mockito.mock(ResultRepository.class);
        feedbackRepository = org.mockito.Mockito.mock(FeedbackRepository.class);
        feedbackService = new FeedbackService(
            resultRepository,
            feedbackRepository,
            Clock.fixed(NOW, ZoneOffset.UTC)
        );
    }

    @Test
    void setManualLabel_setsRelevantForCanonicalAndNormalizedIdentity() {
        ResultItem item = createResultItem(10, null, "https://example.com/jobs/1");
        when(resultRepository.findById(10)).thenReturn(Optional.of(item));

        ManualFeedback feedback = feedbackService.setManualLabel(10, "relevant");

        assertEquals("relevant", feedback.getManualLabel());
        assertEquals("2026-02-15T12:00:00Z", feedback.getManualLabelUpdatedAt());
        verify(feedbackRepository).upsert("canonical:10", "relevant", "2026-02-15T12:00:00Z");
        verify(feedbackRepository).upsert("url:https://example.com/jobs/1", "relevant", "2026-02-15T12:00:00Z");
    }

    @Test
    void setManualLabel_setsIrrelevantUsingCanonicalIdWhenDuplicate() {
        ResultItem item = createResultItem(20, 4, "https://example.com/jobs/2");
        when(resultRepository.findById(20)).thenReturn(Optional.of(item));

        ManualFeedback feedback = feedbackService.setManualLabel(20, "irrelevant");

        assertEquals("irrelevant", feedback.getManualLabel());
        verify(feedbackRepository).upsert("canonical:4", "irrelevant", "2026-02-15T12:00:00Z");
        verify(feedbackRepository).upsert("url:https://example.com/jobs/2", "irrelevant", "2026-02-15T12:00:00Z");
    }

    @Test
    void setManualLabel_clearsToNullAndPersistsTimestamp() {
        ResultItem item = createResultItem(30, null, "https://example.com/jobs/3");
        when(resultRepository.findById(30)).thenReturn(Optional.of(item));

        ManualFeedback feedback = feedbackService.setManualLabel(30, null);

        assertNull(feedback.getManualLabel());
        assertEquals("2026-02-15T12:00:00Z", feedback.getManualLabelUpdatedAt());
        verify(feedbackRepository).upsert("canonical:30", null, "2026-02-15T12:00:00Z");
        verify(feedbackRepository).upsert("url:https://example.com/jobs/3", null, "2026-02-15T12:00:00Z");
    }

    @Test
    void setManualLabel_rejectsInvalidLabel() {
        ResultItem item = createResultItem(40, null, "https://example.com/jobs/4");
        when(resultRepository.findById(40)).thenReturn(Optional.of(item));

        FeedbackValidationException exception = assertThrows(
            FeedbackValidationException.class,
            () -> feedbackService.setManualLabel(40, "not-a-label")
        );

        assertEquals("label must be one of: relevant, irrelevant, or null", exception.getMessage());
        verify(feedbackRepository, never()).upsert(anyString(), anyString(), anyString());
    }

    @Test
    void setManualLabel_throwsNotFoundWhenResultMissing() {
        when(resultRepository.findById(999)).thenReturn(Optional.empty());

        FeedbackNotFoundException exception = assertThrows(
            FeedbackNotFoundException.class,
            () -> feedbackService.setManualLabel(999, "relevant")
        );

        assertEquals("Result not found: 999", exception.getMessage());
    }

    @Test
    void resolveManualFeedback_prefersCanonicalIdentity() {
        ResultItem item = createResultItem(50, 8, "https://example.com/jobs/5");
        when(feedbackRepository.findByIdentityKey("canonical:8"))
            .thenReturn(Optional.of(new ManualFeedback("relevant", "2026-02-14T00:00:00Z")));

        ManualFeedback feedback = feedbackService.resolveManualFeedback(item);

        assertEquals("relevant", feedback.getManualLabel());
        assertEquals("2026-02-14T00:00:00Z", feedback.getManualLabelUpdatedAt());
        verify(feedbackRepository).findByIdentityKey("canonical:8");
        verify(feedbackRepository, never()).findByIdentityKey("url:https://example.com/jobs/5");
    }

    @Test
    void resolveManualFeedback_fallsBackToNormalizedUrl() {
        ResultItem item = createResultItem(60, 9, "https://example.com/jobs/6");
        when(feedbackRepository.findByIdentityKey("canonical:9")).thenReturn(Optional.empty());
        when(feedbackRepository.findByIdentityKey("url:https://example.com/jobs/6"))
            .thenReturn(Optional.of(new ManualFeedback("irrelevant", "2026-02-13T00:00:00Z")));

        ManualFeedback feedback = feedbackService.resolveManualFeedback(item);

        assertEquals("irrelevant", feedback.getManualLabel());
        assertEquals("2026-02-13T00:00:00Z", feedback.getManualLabelUpdatedAt());
    }

    @Test
    void resolveManualFeedback_returnsNullStateWhenUnknown() {
        ResultItem item = createResultItem(70, null, "https://example.com/jobs/7");
        when(feedbackRepository.findByIdentityKey("canonical:70")).thenReturn(Optional.empty());
        when(feedbackRepository.findByIdentityKey("url:https://example.com/jobs/7")).thenReturn(Optional.empty());

        ManualFeedback feedback = feedbackService.resolveManualFeedback(item);

        assertNull(feedback.getManualLabel());
        assertNull(feedback.getManualLabelUpdatedAt());
    }

    private ResultItem createResultItem(Integer id, Integer canonicalId, String normalizedUrl) {
        return new ResultItem(
            id,
            "run-1",
            "query-1",
            "query text",
            "search query",
            "example.com",
            "Title",
            "Snippet",
            "https://example.com/raw",
            "https://example.com/final",
            "2026-02-14T10:00:00Z",
            null,
            null,
            null,
            null,
            null,
            normalizedUrl,
            canonicalId,
            canonicalId != null,
            false,
            0,
            0.5,
            "2026-02-14T10:00:00Z",
            "baseline"
        );
    }
}
