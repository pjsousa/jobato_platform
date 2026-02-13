package com.jobato.api.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

@Service
public class MlRetrainClient {
    private final HttpClient httpClient;
    private final String baseUrl;

    public MlRetrainClient(@Value("${jobato.ml.base-url:${ML_BASE_URL:http://localhost:8000}}") String baseUrl) {
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
        this.baseUrl = baseUrl;
    }

    public ProxyResponse triggerRetrain() {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/ml/retrain/trigger"))
            .timeout(Duration.ofSeconds(60))
            .header("Content-Type", MediaType.APPLICATION_JSON_VALUE)
            .POST(HttpRequest.BodyPublishers.noBody())
            .build();
        return execute(request);
    }

    public ProxyResponse getRetrainStatus() {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/ml/retrain/status"))
            .timeout(Duration.ofSeconds(30))
            .GET()
            .build();
        return execute(request);
    }

    public ProxyResponse getRetrainHistory() {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/ml/retrain/history"))
            .timeout(Duration.ofSeconds(30))
            .GET()
            .build();
        return execute(request);
    }

    private ProxyResponse execute(HttpRequest request) {
        try {
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            return new ProxyResponse(HttpStatus.valueOf(response.statusCode()), response.body());
        } catch (IOException | InterruptedException exception) {
            if (exception instanceof InterruptedException) {
                Thread.currentThread().interrupt();
            }
            throw new IllegalStateException("Failed to reach ML retrain service", exception);
        }
    }

    public record ProxyResponse(HttpStatus status, String body) {}
}
