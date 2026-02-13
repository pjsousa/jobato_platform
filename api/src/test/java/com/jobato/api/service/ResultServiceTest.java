package com.jobato.api.service;

import com.jobato.api.model.ResultItem;
import com.jobato.api.repository.ResultRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class ResultServiceTest {

    private ResultRepository resultRepository;
    private ResultService resultService;

    @BeforeEach
    void setUp() {
        resultRepository = mock(ResultRepository.class);
        resultService = new ResultService(resultRepository);
    }

    @Test
    void getVisibleResultsForRun_excludesHidden() {
        // Arrange
        String runId = "test-run-1";
        List<ResultItem> visibleResults = Arrays.asList(
            createResultItem(1, runId, false, false),
            createResultItem(2, runId, false, false)
        );
        when(resultRepository.findVisibleForRun(runId)).thenReturn(visibleResults);

        // Act
        List<ResultItem> results = resultService.getVisibleResultsForRun(runId);

        // Assert
        assertEquals(2, results.size());
        verify(resultRepository).findVisibleForRun(runId);
    }

    @Test
    void getAllResultsForRun_includesHidden() {
        // Arrange
        String runId = "test-run-1";
        List<ResultItem> allResults = Arrays.asList(
            createResultItem(1, runId, false, false),
            createResultItem(2, runId, true, true)
        );
        when(resultRepository.findAllForRun(runId)).thenReturn(allResults);

        // Act
        List<ResultItem> results = resultService.getAllResultsForRun(runId);

        // Assert
        assertEquals(2, results.size());
        verify(resultRepository).findAllForRun(runId);
    }

    @Test
    void getResultsForRun_withIncludeHiddenFalse() {
        // Arrange
        String runId = "test-run-1";
        List<ResultItem> results = Arrays.asList(createResultItem(1, runId, false, false));
        when(resultRepository.findByRunId(runId, false)).thenReturn(results);

        // Act
        List<ResultItem> returned = resultService.getResultsForRun(runId, false);

        // Assert
        assertEquals(1, returned.size());
        verify(resultRepository).findByRunId(runId, false);
    }

    @Test
    void getResultsForRun_withIncludeHiddenTrue() {
        // Arrange
        String runId = "test-run-1";
        List<ResultItem> results = Arrays.asList(
            createResultItem(1, runId, false, false),
            createResultItem(2, runId, true, true)
        );
        when(resultRepository.findByRunId(runId, true)).thenReturn(results);

        // Act
        List<ResultItem> returned = resultService.getResultsForRun(runId, true);

        // Assert
        assertEquals(2, returned.size());
        verify(resultRepository).findByRunId(runId, true);
    }

    @Test
    void getResultById_returnsResult() {
        // Arrange
        Integer resultId = 1;
        ResultItem result = createResultItem(resultId, "test-run", false, false);
        when(resultRepository.findById(resultId)).thenReturn(Optional.of(result));

        // Act
        Optional<ResultItem> returned = resultService.getResultById(resultId);

        // Assert
        assertTrue(returned.isPresent());
        assertEquals(resultId, returned.get().getId());
    }

    @Test
    void getResultById_returnsEmptyForMissing() {
        // Arrange
        Integer resultId = 999;
        when(resultRepository.findById(resultId)).thenReturn(Optional.empty());

        // Act
        Optional<ResultItem> returned = resultService.getResultById(resultId);

        // Assert
        assertFalse(returned.isPresent());
    }

    @Test
    void getResultsForRunAndQuery_withIncludeHidden() {
        // Arrange
        String runId = "test-run";
        String queryId = "q1";
        List<ResultItem> results = Arrays.asList(createResultItem(1, runId, false, false));
        when(resultRepository.findByRunIdAndQueryId(runId, queryId, false)).thenReturn(results);

        // Act
        List<ResultItem> returned = resultService.getResultsForRunAndQuery(runId, queryId, false);

        // Assert
        assertEquals(1, returned.size());
        verify(resultRepository).findByRunIdAndQueryId(runId, queryId, false);
    }

    @Test
    void countResultsForRun_excludesHidden() {
        // Arrange
        String runId = "test-run";
        when(resultRepository.countByRunId(runId, false)).thenReturn(10);

        // Act
        int count = resultService.countResultsForRun(runId, false);

        // Assert
        assertEquals(10, count);
        verify(resultRepository).countByRunId(runId, false);
    }

    @Test
    void countDuplicatesForRun_returnsCount() {
        // Arrange
        String runId = "test-run";
        when(resultRepository.countDuplicatesForRun(runId)).thenReturn(5);

        // Act
        int count = resultService.countDuplicatesForRun(runId);

        // Assert
        assertEquals(5, count);
        verify(resultRepository).countDuplicatesForRun(runId);
    }

    @Test
    void getCanonicalRecord_returnsCanonical() {
        // Arrange
        Integer duplicateId = 2;
        Integer canonicalId = 1;
        ResultItem duplicate = createResultItem(duplicateId, "test-run", true, true, canonicalId);
        ResultItem canonical = createResultItem(canonicalId, "test-run", false, false, null);
        
        when(resultRepository.findById(duplicateId)).thenReturn(Optional.of(duplicate));
        when(resultRepository.findById(canonicalId)).thenReturn(Optional.of(canonical));

        // Act
        Optional<ResultItem> returned = resultService.getCanonicalRecord(duplicateId);

        // Assert
        assertTrue(returned.isPresent());
        assertEquals(canonicalId, returned.get().getId());
    }

    @Test
    void getCanonicalRecord_returnsEmptyForNonDuplicate() {
        // Arrange
        Integer resultId = 1;
        ResultItem result = createResultItem(resultId, "test-run", false, false, null);
        when(resultRepository.findById(resultId)).thenReturn(Optional.of(result));

        // Act
        Optional<ResultItem> returned = resultService.getCanonicalRecord(resultId);

        // Assert
        assertFalse(returned.isPresent());
    }

    @Test
    void getCanonicalRecord_returnsEmptyWhenCanonicalNotFound() {
        // Arrange
        Integer duplicateId = 2;
        Integer canonicalId = 999;
        ResultItem duplicate = createResultItem(duplicateId, "test-run", true, true, canonicalId);
        
        when(resultRepository.findById(duplicateId)).thenReturn(Optional.of(duplicate));
        when(resultRepository.findById(canonicalId)).thenReturn(Optional.empty());

        // Act
        Optional<ResultItem> returned = resultService.getCanonicalRecord(duplicateId);

        // Assert
        assertFalse(returned.isPresent());
    }

    private ResultItem createResultItem(int id, String runId, boolean isDuplicate, boolean isHidden) {
        return createResultItem(id, runId, isDuplicate, isHidden, null);
    }

    private ResultItem createResultItem(int id, String runId, boolean isDuplicate, boolean isHidden, Integer canonicalId) {
        return new ResultItem(
            id, runId, "q1", "test query", "site:example.com test", "example.com",
            "Test Job " + id, "Test snippet", "https://example.com/job/" + id,
            "https://example.com/job/" + id, "2026-02-13T10:00:00Z",
            null, null, null, null, null, "hash" + id,
            canonicalId, isDuplicate, isHidden, isDuplicate ? 0 : 1
        );
    }
}
