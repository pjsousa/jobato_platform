package com.jobato.api.controller;

import com.jobato.api.service.MlEvaluationClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/ml/evaluations")
public class MlEvaluationController {
    private final MlEvaluationClient mlEvaluationClient;

    public MlEvaluationController(MlEvaluationClient mlEvaluationClient) {
        this.mlEvaluationClient = mlEvaluationClient;
    }

    @PostMapping
    public ResponseEntity<String> triggerEvaluation() {
        MlEvaluationClient.ProxyResponse response = mlEvaluationClient.triggerEvaluation();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @GetMapping("/{evaluationId}")
    public ResponseEntity<String> getEvaluationStatus(@PathVariable String evaluationId) {
        MlEvaluationClient.ProxyResponse response = mlEvaluationClient.getEvaluationStatus(evaluationId);
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @GetMapping("/{evaluationId}/results")
    public ResponseEntity<String> getEvaluationResults(@PathVariable String evaluationId) {
        MlEvaluationClient.ProxyResponse response = mlEvaluationClient.getEvaluationResults(evaluationId);
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }
}
