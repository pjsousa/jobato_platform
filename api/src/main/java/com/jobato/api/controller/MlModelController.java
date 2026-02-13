package com.jobato.api.controller;

import com.jobato.api.service.MlModelClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/ml/models")
public class MlModelController {
    private final MlModelClient mlModelClient;

    public MlModelController(MlModelClient mlModelClient) {
        this.mlModelClient = mlModelClient;
    }

    @GetMapping("/comparisons")
    public ResponseEntity<String> getComparisons() {
        MlModelClient.ProxyResponse response = mlModelClient.getComparisons();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @PostMapping("/{modelId}/activate")
    public ResponseEntity<String> activateModel(@PathVariable String modelId) {
        MlModelClient.ProxyResponse response = mlModelClient.activateModel(modelId);
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @PostMapping("/{modelId}/rollback")
    public ResponseEntity<String> rollbackModel(@PathVariable String modelId) {
        MlModelClient.ProxyResponse response = mlModelClient.rollbackModel(modelId);
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @GetMapping("/active")
    public ResponseEntity<String> getActiveModel() {
        MlModelClient.ProxyResponse response = mlModelClient.getActiveModel();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @GetMapping("/history")
    public ResponseEntity<String> getHistory() {
        MlModelClient.ProxyResponse response = mlModelClient.getHistory();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }
}
