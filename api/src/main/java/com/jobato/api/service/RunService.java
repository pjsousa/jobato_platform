package com.jobato.api.service;

import com.jobato.api.dto.RunInput;
import com.jobato.api.dto.RunRequestedPayload;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RunService {
    private final RunInputService runInputService;

    public RunService(RunInputService runInputService) {
        this.runInputService = runInputService;
    }

    public RunRequestedPayload prepareRunRequestedPayload() {
        List<RunInput> runInputs = runInputService.buildRunInputs();
        return new RunRequestedPayload(runInputs);
    }
}
