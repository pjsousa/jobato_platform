package com.jobato.api.controller;

import com.jobato.api.model.ResultItem;
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
    private ResultsController resultsController;

    @BeforeEach
    void setUp() {
        resultService = mock(ResultService.class);
        resultsController = new ResultsController(resultService);
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
