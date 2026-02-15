package com.jobato.api.service;

import com.jobato.api.model.ResultItem;
import com.jobato.api.repository.ResultRepository;
import com.jobato.api.repository.RunSummaryRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class ResultService {
    private final ResultRepository resultRepository;
    private final RunSummaryRepository runSummaryRepository;

    public ResultService(ResultRepository resultRepository, RunSummaryRepository runSummaryRepository) {
        this.resultRepository = resultRepository;
        this.runSummaryRepository = runSummaryRepository;
    }

    public List<ResultItem> getResults(String runId, String view, boolean includeHidden) {
        if (runId != null && !runId.isBlank()) {
            return resultRepository.findByRunId(runId, includeHidden);
        }

        if ("all-time".equals(view)) {
            return resultRepository.findAll(includeHidden);
        }

        return runSummaryRepository.findLatest()
            .map(summary -> resultRepository.findByRunId(summary.getRunId(), includeHidden))
            .orElseGet(List::of);
    }

    /**
     * Get results for a run, excluding hidden duplicates by default.
     * 
     * @param runId the run ID
     * @param includeHidden whether to include hidden duplicates (default: false)
     * @return list of results
     */
    public List<ResultItem> getResultsForRun(String runId, boolean includeHidden) {
        return resultRepository.findByRunId(runId, includeHidden);
    }

    /**
     * Get results for a run, excluding hidden duplicates.
     * This is the default behavior as per AC3.
     * 
     * @param runId the run ID
     * @return list of visible results
     */
    public List<ResultItem> getVisibleResultsForRun(String runId) {
        return resultRepository.findVisibleForRun(runId);
    }

    /**
     * Get all results for a run, including hidden duplicates.
     * 
     * @param runId the run ID
     * @return list of all results
     */
    public List<ResultItem> getAllResultsForRun(String runId) {
        return resultRepository.findAllForRun(runId);
    }

    /**
     * Get a single result by ID.
     * 
     * @param id the result ID
     * @return optional containing the result if found
     */
    public Optional<ResultItem> getResultById(Integer id) {
        return resultRepository.findById(id);
    }

    /**
     * Get results for a specific run and query.
     * 
     * @param runId the run ID
     * @param queryId the query ID
     * @param includeHidden whether to include hidden duplicates
     * @return list of results
     */
    public List<ResultItem> getResultsForRunAndQuery(String runId, String queryId, boolean includeHidden) {
        return resultRepository.findByRunIdAndQueryId(runId, queryId, includeHidden);
    }

    /**
     * Count results for a run.
     * 
     * @param runId the run ID
     * @param includeHidden whether to include hidden duplicates
     * @return count of results
     */
    public int countResultsForRun(String runId, boolean includeHidden) {
        return resultRepository.countByRunId(runId, includeHidden);
    }

    /**
     * Count duplicate results for a run.
     * 
     * @param runId the run ID
     * @return count of duplicates
     */
    public int countDuplicatesForRun(String runId) {
        return resultRepository.countDuplicatesForRun(runId);
    }

    /**
     * Get the canonical record for a duplicate result.
     * 
     * @param resultId the duplicate result ID
     * @return optional containing the canonical result if found
     */
    public Optional<ResultItem> getCanonicalRecord(Integer resultId) {
        Optional<ResultItem> result = resultRepository.findById(resultId);
        if (result.isPresent() && result.get().getCanonicalId() != null) {
            return resultRepository.findById(result.get().getCanonicalId());
        }
        return Optional.empty();
    }
}
