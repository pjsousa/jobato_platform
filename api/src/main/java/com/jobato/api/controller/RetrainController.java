package com.jobato.api.controller;

import com.jobato.api.service.MlRetrainClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/ml/retrain")
public class RetrainController {
    private final MlRetrainClient mlRetrainClient;

    public RetrainController(MlRetrainClient mlRetrainClient) {
        this.mlRetrainClient = mlRetrainClient;
    }

    @PostMapping("/trigger")
    public ResponseEntity<String> triggerRetrain() {
        MlRetrainClient.ProxyResponse response = mlRetrainClient.triggerRetrain();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @GetMapping("/status")
    public ResponseEntity<String> getStatus() {
        MlRetrainClient.ProxyResponse response = mlRetrainClient.getRetrainStatus();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }

    @GetMapping("/history")
    public ResponseEntity<String> getHistory() {
        MlRetrainClient.ProxyResponse response = mlRetrainClient.getRetrainHistory();
        return ResponseEntity.status(response.status())
            .contentType(MediaType.APPLICATION_JSON)
            .body(response.body());
    }
}
