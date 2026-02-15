package com.jobato.api.controller;

import com.jobato.api.model.ResultItem;
import com.jobato.api.model.ManualFeedback;
import com.jobato.api.service.FeedbackService;
import com.jobato.api.service.ResultService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class ResultsControllerTest {

    private ResultService resultService;
    private FeedbackService feedbackService;
    private ResultsController resultsController;

    @BeforeEach
    void setUp() {
        resultService = mock(ResultService.class);
        feedbackService = mock(FeedbackService.class);
        when(feedbackService.resolveManualFeedback(any(ResultItem.class))).thenReturn(new ManualFeedback(null, null));
        resultsController = new ResultsController(resultService, feedbackService);
    }

    @Test
    void getResults_excludesHiddenByDefault() {
        // Arrange
        String runId = "test-run-1";
        List<ResultItem> visibleResults = Arrays.asList(
            createResultItem(1, runId, false),
            createResultItem(2, runId, false)
        );
        when(resultService.getResults(runId, "today", false)).thenReturn(visibleResults);

        // Act
        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(runId, "today", null);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(2, response.getBody().size());
        verify(resultService).getResults(runId, "today", false);
        verify(feedbackService, times(2)).resolveManualFeedback(any(ResultItem.class));
    }

    @Test
    void getResults_includesHiddenWhenRequested() {
        // Arrange
        String runId = "test-run-1";
        List<ResultItem> allResults = Arrays.asList(
            createResultItem(1, runId, false),
            createResultItem(2, runId, true)
        );
        when(resultService.getResults(runId, "today", true)).thenReturn(allResults);

        // Act
        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(runId, "today", true);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(2, response.getBody().size());
        verify(resultService).getResults(runId, "today", true);
        verify(feedbackService, times(2)).resolveManualFeedback(any(ResultItem.class));
    }

    @Test
    void getResults_returnsDedupeFields() {
        // Arrange
        String runId = "test-run-1";
        ResultItem result = new ResultItem(
            1, runId, "q1", "test query", "site:example.com test", "example.com",
            "Test Job", "Test snippet", "https://example.com/job/1", "https://example.com/job/1",
            "2026-02-13T10:00:00Z", null, null, null, null, null, "hash123",
            null, false, false, 2,  // canonicalId, isDuplicate, isHidden, duplicateCount
            0.0, "2026-02-13T10:00:00Z", "baseline"  // relevanceScore, scoredAt, scoreVersion
        );
        when(resultService.getResults(runId, "today", false)).thenReturn(Arrays.asList(result));

        // Act
        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(runId, "today", false);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> resultMap = response.getBody().get(0);
        assertEquals(1, resultMap.get("id"));
        assertEquals(false, resultMap.get("isDuplicate"));
        assertEquals(false, resultMap.get("isHidden"));
        assertEquals(2, resultMap.get("duplicateCount"));
        assertNull(resultMap.get("canonicalId"));
        assertNull(resultMap.get("manualLabel"));
        assertNull(resultMap.get("manualLabelUpdatedAt"));
    }

    @Test
    void getResultById_returnsCanonicalLinkForDuplicate() {
        // Arrange
        Integer duplicateId = 2;
        Integer canonicalId = 1;
        ResultItem duplicate = new ResultItem(
            duplicateId, "test-run", "q1", "test", "site:example.com test", "example.com",
            "Duplicate Job", "Duplicate snippet", "https://example.com/job/2", "https://example.com/job/2",
            "2026-02-13T10:00:00Z", null, null, null, null, null, "hash2",
            canonicalId, true, true, 0,
            null, null, null  // relevanceScore, scoredAt, scoreVersion - duplicates inherit
        );
        ResultItem canonical = new ResultItem(
            canonicalId, "test-run", "q1", "test", "site:example.com test", "example.com",
            "Canonical Job", "Canonical snippet", "https://example.com/job/1", "https://example.com/job/1",
            "2026-02-13T09:00:00Z", null, null, null, null, null, "hash1",
            null, false, false, 1,
            0.5, "2026-02-13T09:00:00Z", "baseline"  // relevanceScore, scoredAt, scoreVersion
        );
        when(resultService.getResultById(duplicateId)).thenReturn(Optional.of(duplicate));
        when(resultService.getCanonicalRecord(duplicateId)).thenReturn(Optional.of(canonical));

        // Act
        ResponseEntity<Map<String, Object>> response = resultsController.getResultById(duplicateId);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> resultMap = response.getBody();
        assertEquals(canonicalId, resultMap.get("canonicalId"));
        assertEquals(true, resultMap.get("isDuplicate"));
        assertEquals(true, resultMap.get("isHidden"));
        assertNotNull(resultMap.get("canonicalRecord"));
        assertNull(resultMap.get("manualLabel"));
        
        @SuppressWarnings("unchecked")
        Map<String, Object> canonicalRecord = (Map<String, Object>) resultMap.get("canonicalRecord");
        assertEquals(canonicalId, canonicalRecord.get("id"));
    }

    @Test
    void getResultById_returnsNotFoundForMissingResult() {
        // Arrange
        Integer resultId = 999;
        when(resultService.getResultById(resultId)).thenReturn(Optional.empty());

        // Act
        ResponseEntity<Map<String, Object>> response = resultsController.getResultById(resultId);

        // Assert
        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    void getResultsByQuery_filtersByQueryId() {
        // Arrange
        String runId = "test-run-1";
        String queryId = "q1";
        List<ResultItem> results = Arrays.asList(
            createResultItem(1, runId, false),
            createResultItem(2, runId, false)
        );
        when(resultService.getResultsForRunAndQuery(runId, queryId, false)).thenReturn(results);

        // Act
        ResponseEntity<List<Map<String, Object>>> response = 
            resultsController.getResultsByQuery(runId, queryId, null);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(2, response.getBody().size());
        verify(resultService).getResultsForRunAndQuery(runId, queryId, false);
    }

    @Test
    void getResultsByQuery_includesHiddenWhenRequestedAndPreservesOrder() {
        String runId = "test-run-1";
        String queryId = "q1";
        ResultItem first = new ResultItem(
            9, runId, queryId, "query one", "site:example.com query one", "example.com",
            "Newest", "Newest snippet", "https://example.com/job/9", "https://example.com/job/9",
            "2026-02-14T10:00:00Z", null, null, "cache-9", null, "2026-02-15T11:00:00Z", "https://example.com/job/9",
            null, false, false, 0,
            0.9, "2026-02-14T10:00:00Z", "baseline"
        );
        ResultItem second = new ResultItem(
            8, runId, queryId, "query one", "site:example.com query one", "example.com",
            "Hidden duplicate", "Hidden snippet", "https://example.com/job/8", "https://example.com/job/8",
            "2026-02-14T09:00:00Z", null, null, "cache-8", null, "2026-02-15T11:00:00Z", "https://example.com/job/8",
            9, true, true, 0,
            null, null, null
        );
        when(resultService.getResultsForRunAndQuery(runId, queryId, true)).thenReturn(Arrays.asList(first, second));

        ResponseEntity<List<Map<String, Object>>> response =
            resultsController.getResultsByQuery(runId, queryId, true);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(List.of(9, 8), response.getBody().stream().map(item -> (Integer) item.get("id")).toList());
        assertEquals("2026-02-14T10:00:00Z", response.getBody().get(0).get("createdAt"));
        assertEquals("2026-02-15T11:00:00Z", response.getBody().get(0).get("lastSeenAt"));
        assertFalse(response.getBody().get(0).containsKey("created_at"));
        assertFalse(response.getBody().get(0).containsKey("last_seen_at"));
        verify(resultService).getResultsForRunAndQuery(runId, queryId, true);
    }

    @Test
    void getResultCounts_returnsCorrectCounts() {
        // Arrange
        String runId = "test-run-1";
        when(resultService.countResultsForRun(runId, false)).thenReturn(10);
        when(resultService.countDuplicatesForRun(runId)).thenReturn(3);

        // Act
        ResponseEntity<Map<String, Object>> response = resultsController.getResultCounts(runId, false);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> counts = response.getBody();
        assertEquals(runId, counts.get("runId"));
        assertEquals(10, counts.get("totalCount"));
        assertEquals(3, counts.get("duplicateCount"));
        assertEquals(false, counts.get("includeHidden"));
    }

    @Test
    void getResults_returnsScoringFields() {
        // Arrange
        String runId = "test-run-1";
        ResultItem result = new ResultItem(
            1, runId, "q1", "test query", "site:example.com test", "example.com",
            "Test Job", "Test snippet", "https://example.com/job/1", "https://example.com/job/1",
            "2026-02-13T10:00:00Z", null, null, null, null, null, "hash123",
            null, false, false, 0,
            0.75, "2026-02-13T10:00:00Z", "baseline"
        );
        when(resultService.getResults(runId, "today", false)).thenReturn(Arrays.asList(result));

        // Act
        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(runId, "today", false);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> resultMap = response.getBody().get(0);
        assertEquals(0.75, resultMap.get("relevanceScore"));
        assertEquals("2026-02-13T10:00:00Z", resultMap.get("scoredAt"));
        assertEquals("baseline", resultMap.get("scoreVersion"));
        assertNull(resultMap.get("manualLabel"));
    }

    @Test
    void getResults_returnsNullScoringFieldsWhenNotScored() {
        // Arrange
        String runId = "test-run-1";
        ResultItem result = new ResultItem(
            1, runId, "q1", "test query", "site:example.com test", "example.com",
            "Test Job", "Test snippet", "https://example.com/job/1", "https://example.com/job/1",
            "2026-02-13T10:00:00Z", null, null, null, null, null, "hash123",
            null, false, false, 0,
            null, null, null  // Not yet scored
        );
        when(resultService.getResults(runId, "today", false)).thenReturn(Arrays.asList(result));

        // Act
        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(runId, "today", false);

        // Assert
        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> resultMap = response.getBody().get(0);
        assertNull(resultMap.get("relevanceScore"));
        assertNull(resultMap.get("scoredAt"));
        assertNull(resultMap.get("scoreVersion"));
        assertNull(resultMap.get("manualLabel"));
    }

    @Test
    void getResults_returnsManualLabelFieldsWhenHydrated() {
        String runId = "test-run-1";
        ResultItem result = createResultItem(1, runId, false);
        when(resultService.getResults(runId, "today", false)).thenReturn(List.of(result));
        when(feedbackService.resolveManualFeedback(result))
            .thenReturn(new ManualFeedback("relevant", "2026-02-15T12:00:00Z"));

        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(runId, "today", false);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> resultMap = response.getBody().get(0);
        assertEquals("relevant", resultMap.get("manualLabel"));
        assertEquals("2026-02-15T12:00:00Z", resultMap.get("manualLabelUpdatedAt"));
    }

    @Test
    void getResults_defaultsToTodayView() {
        when(resultService.getResults(null, "today", false)).thenReturn(List.of());

        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(null, "today", null);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        verify(resultService).getResults(null, "today", false);
    }

    @Test
    void getResults_supportsAllTimeView() {
        when(resultService.getResults(null, "all-time", false)).thenReturn(List.of());

        ResponseEntity<List<Map<String, Object>>> response = resultsController.getResults(null, "all-time", false);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        verify(resultService).getResults(null, "all-time", false);
    }

    private ResultItem createResultItem(int id, String runId, boolean isHidden) {
        return new ResultItem(
            id, runId, "q1", "test query", "site:example.com test", "example.com",
            "Test Job " + id, "Test snippet", "https://example.com/job/" + id,
            "https://example.com/job/" + id, "2026-02-13T10:00:00Z",
            null, null, null, null, null, "hash" + id,
            null, false, isHidden, 0,
            0.0, "2026-02-13T10:00:00Z", "baseline"
        );
    }
}
