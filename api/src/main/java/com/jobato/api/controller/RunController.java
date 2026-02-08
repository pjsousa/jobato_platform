package com.jobato.api.controller;

import com.jobato.api.dto.RunResponse;
import com.jobato.api.service.RunService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/runs")
public class RunController {
    private final RunService runService;

    public RunController(RunService runService) {
        this.runService = runService;
    }

    @PostMapping
    public ResponseEntity<RunResponse> triggerRun() {
        RunResponse response = runService.triggerRun();
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{id}")
    public RunResponse getRun(@PathVariable String id) {
        return runService.getRun(id);
    }
}
