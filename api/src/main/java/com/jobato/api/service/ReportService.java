package com.jobato.api.service;

import com.jobato.api.model.RunSummary;
import com.jobato.api.repository.RunSummaryRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

@Service
public class ReportService {
    private final RunSummaryRepository runSummaryRepository;

    public ReportService(RunSummaryRepository runSummaryRepository) {
        this.runSummaryRepository = runSummaryRepository;
    }

    public void saveRunSummary(String runId, Instant triggerTime, Long durationMs, 
                               Integer newJobsCount, Integer relevantCount, String status) {
        RunSummary runSummary = new RunSummary(runId, triggerTime, durationMs, newJobsCount, relevantCount, status);
        runSummaryRepository.save(runSummary);
    }

    public Optional<RunSummary> getLatestRunSummary() {
        return runSummaryRepository.findLatest();
    }
}