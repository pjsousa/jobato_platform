package com.jobato.api.service;

import com.jobato.api.model.RunSummary;
import com.jobato.api.repository.RunSummaryRepository;
import com.jobato.api.model.ZeroResultLog;
import com.jobato.api.repository.ZeroResultLogRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
public class ReportService {
    private final RunSummaryRepository runSummaryRepository;
    private final ZeroResultLogRepository zeroResultLogRepository;

    public ReportService(RunSummaryRepository runSummaryRepository,
                         ZeroResultLogRepository zeroResultLogRepository) {
        this.runSummaryRepository = runSummaryRepository;
        this.zeroResultLogRepository = zeroResultLogRepository;
    }

    public void saveRunSummary(String runId, Instant triggerTime, Long durationMs, 
                               Integer newJobsCount, Integer relevantCount, String status) {
        RunSummary runSummary = new RunSummary(runId, triggerTime, durationMs, newJobsCount, relevantCount, status);
        runSummaryRepository.save(runSummary);
    }

    public void saveZeroResultLogs(List<ZeroResultLog> logs) {
        zeroResultLogRepository.saveAll(logs);
    }

    public Optional<RunSummary> getLatestRunSummary() {
        return runSummaryRepository.findLatest();
    }

    public List<ZeroResultLog> getZeroResultLogsForRun(String runId) {
        return zeroResultLogRepository.findByRunId(runId);
    }
}
