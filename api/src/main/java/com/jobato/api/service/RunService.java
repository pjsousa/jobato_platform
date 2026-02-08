package com.jobato.api.service;

import com.jobato.api.dto.RunInput;
import com.jobato.api.dto.RunRequestedPayload;
import com.jobato.api.dto.RunResponse;
import com.jobato.api.messaging.RunEventPublisher;
import com.jobato.api.model.RunRecord;
import com.jobato.api.repository.RunRepository;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class RunService {
    private final RunInputService runInputService;
    private final RunRepository runRepository;
    private final RunEventPublisher runEventPublisher;
    private final QuotaService quotaService;
    private final Clock clock;

    public RunService(RunInputService runInputService,
                      RunRepository runRepository,
                      RunEventPublisher runEventPublisher,
                      QuotaService quotaService,
                      Clock clock) {
        this.runInputService = runInputService;
        this.runRepository = runRepository;
        this.runEventPublisher = runEventPublisher;
        this.quotaService = quotaService;
        this.clock = clock;
    }

    public RunRequestedPayload prepareRunRequestedPayload() {
        List<RunInput> runInputs = runInputService.buildRunInputs();
        return new RunRequestedPayload(runInputs);
    }

    public RunResponse triggerRun() {
        runRepository.findActiveRun().ifPresent(run -> {
            throw new RunInProgressException("A run is already in progress. Please wait for it to finish before starting another.");
        });

        quotaService.ensureQuotaAvailable();

        RunRequestedPayload payload = prepareRunRequestedPayload();
        String runId = UUID.randomUUID().toString();
        Instant startedAt = Instant.now(clock);
        RunRecord runRecord = runRepository.createRun(runId, startedAt);
        runEventPublisher.publishRunRequested(runId, payload, startedAt);
        return toResponse(runRecord);
    }

    public RunResponse getRun(String runId) {
        RunRecord record = runRepository.findById(runId)
            .orElseThrow(() -> new RunNotFoundException("Run not found"));
        return toResponse(record);
    }

    private RunResponse toResponse(RunRecord record) {
        String endedAt = record.endedAt() == null ? null : record.endedAt().toString();
        return new RunResponse(
            record.runId(),
            record.status(),
            record.startedAt().toString(),
            endedAt,
            record.statusReason()
        );
    }
}
