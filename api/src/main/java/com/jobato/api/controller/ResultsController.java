package com.jobato.api.controller;

import com.jobato.api.model.ResultItem;
import com.jobato.api.service.ResultService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/results")
public class ResultsController {
    private final ResultService resultService;

    public ResultsController(ResultService resultService) {
        this.resultService = resultService;
    }

    /**
     * Get results for a run.
     * By default, excludes hidden duplicates (AC3).
     * Use ?includeHidden=true to include duplicates.
     */
    @GetMapping
    public ResponseEntity<List<Map<String, Object>>> getResults(
            @RequestParam String runId,
            @RequestParam(required = false) Boolean includeHidden) {
        
        boolean shouldIncludeHidden = includeHidden != null && includeHidden;
        List<ResultItem> results = resultService.getResultsForRun(runId, shouldIncludeHidden);
        
        List<Map<String, Object>> response = results.stream()
            .map(this::toResponse)
            .collect(Collectors.toList());
        
        return ResponseEntity.ok(response);
    }

    /**
     * Get a single result by ID.
     * Returns the result with its canonical link if applicable.
     */
    @GetMapping("/{id}")
    public ResponseEntity<Map<String, Object>> getResultById(@PathVariable Integer id) {
        Optional<ResultItem> result = resultService.getResultById(id);
        
        if (result.isPresent()) {
            Map<String, Object> response = toResponse(result.get());
            
            // Include canonical record data if this is a duplicate
            if (result.get().getCanonicalId() != null) {
                Optional<ResultItem> canonical = resultService.getCanonicalRecord(id);
                canonical.ifPresent(c -> response.put("canonicalRecord", toCanonicalResponse(c)));
            }
            
            return ResponseEntity.ok(response);
        }
        
        return ResponseEntity.notFound().build();
    }

    /**
     * Get results for a specific run and query.
     * By default, excludes hidden duplicates.
     */
    @GetMapping("/by-query")
    public ResponseEntity<List<Map<String, Object>>> getResultsByQuery(
            @RequestParam String runId,
            @RequestParam String queryId,
            @RequestParam(required = false) Boolean includeHidden) {
        
        boolean shouldIncludeHidden = includeHidden != null && includeHidden;
        List<ResultItem> results = resultService.getResultsForRunAndQuery(runId, queryId, shouldIncludeHidden);
        
        List<Map<String, Object>> response = results.stream()
            .map(this::toResponse)
            .collect(Collectors.toList());
        
        return ResponseEntity.ok(response);
    }

    /**
     * Get result counts for a run.
     */
    @GetMapping("/counts")
    public ResponseEntity<Map<String, Object>> getResultCounts(
            @RequestParam String runId,
            @RequestParam(required = false) Boolean includeHidden) {
        
        boolean shouldIncludeHidden = includeHidden != null && includeHidden;
        int totalCount = resultService.countResultsForRun(runId, shouldIncludeHidden);
        int duplicateCount = resultService.countDuplicatesForRun(runId);
        
        Map<String, Object> response = new HashMap<>();
        response.put("runId", runId);
        response.put("totalCount", totalCount);
        response.put("duplicateCount", duplicateCount);
        response.put("includeHidden", shouldIncludeHidden);
        
        return ResponseEntity.ok(response);
    }

    private Map<String, Object> toResponse(ResultItem result) {
        Map<String, Object> response = new HashMap<>();
        response.put("id", result.getId());
        response.put("runId", result.getRunId());
        response.put("queryId", result.getQueryId());
        response.put("queryText", result.getQueryText());
        response.put("searchQuery", result.getSearchQuery());
        response.put("domain", result.getDomain());
        response.put("title", result.getTitle());
        response.put("snippet", result.getSnippet());
        response.put("rawUrl", result.getRawUrl());
        response.put("finalUrl", result.getFinalUrl());
        response.put("createdAt", result.getCreatedAt());
        response.put("rawHtmlPath", result.getRawHtmlPath());
        response.put("visibleText", result.getVisibleText());
        response.put("cacheKey", result.getCacheKey());
        response.put("cachedAt", result.getCachedAt());
        response.put("lastSeenAt", result.getLastSeenAt());
        response.put("normalizedUrl", result.getNormalizedUrl());
        // Dedupe fields - camelCase for API
        response.put("canonicalId", result.getCanonicalId());
        response.put("isDuplicate", result.getIsDuplicate());
        response.put("isHidden", result.getIsHidden());
        response.put("duplicateCount", result.getDuplicateCount());
        return response;
    }

    private Map<String, Object> toCanonicalResponse(ResultItem result) {
        // Simplified response for canonical record reference
        Map<String, Object> response = new HashMap<>();
        response.put("id", result.getId());
        response.put("title", result.getTitle());
        response.put("snippet", result.getSnippet());
        response.put("finalUrl", result.getFinalUrl());
        response.put("domain", result.getDomain());
        response.put("duplicateCount", result.getDuplicateCount());
        return response;
    }
}
