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
public class MlEvaluationClient {
    private final HttpClient httpClient;
    private final String baseUrl;

    public MlEvaluationClient(@Value("${jobato.ml.base-url:${ML_BASE_URL:http://localhost:8000}}") String baseUrl) {
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
        this.baseUrl = baseUrl;
    }

    public ProxyResponse triggerEvaluation() {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/ml/evaluations"))
            .timeout(Duration.ofSeconds(30))
            .header("Content-Type", MediaType.APPLICATION_JSON_VALUE)
            .POST(HttpRequest.BodyPublishers.noBody())
            .build();
        return execute(request);
    }

    public ProxyResponse getEvaluationStatus(String evaluationId) {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/ml/evaluations/" + evaluationId))
            .timeout(Duration.ofSeconds(30))
            .GET()
            .build();
        return execute(request);
    }

    public ProxyResponse getEvaluationResults(String evaluationId) {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/ml/evaluations/" + evaluationId + "/results"))
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
            throw new IllegalStateException("Failed to reach ML evaluation service", exception);
        }
    }

    public record ProxyResponse(HttpStatus status, String body) {}
}
