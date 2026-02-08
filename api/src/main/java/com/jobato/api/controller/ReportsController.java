package com.jobato.api.controller;

import com.jobato.api.model.RunSummary;
import com.jobato.api.service.ReportService;
import com.jobato.api.dto.RunSummaryResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

@RestController
@RequestMapping("/api/reports")
public class ReportsController {
    private final ReportService reportService;

    public ReportsController(ReportService reportService) {
        this.reportService = reportService;
    }

    @GetMapping("/runs/latest")
    public ResponseEntity<RunSummaryResponse> getLatestRunSummary() {
        Optional<RunSummary> summary = reportService.getLatestRunSummary();
        if (summary.isPresent()) {
            return ResponseEntity.ok(toResponse(summary.get()));
        }
        return ResponseEntity.noContent().build();
    }

    private RunSummaryResponse toResponse(RunSummary summary) {
        return new RunSummaryResponse(
            summary.getRunId(),
            summary.getStatus(),
            summary.getTriggerTime().toString(),
            summary.getDurationMs(),
            summary.getNewJobsCount(),
            summary.getRelevantCount()
        );
    }
}