package com.jobato.api.service;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

import static org.junit.jupiter.api.Assertions.assertEquals;

class MlModelClientTest {

    private HttpServer server;
    private String baseUrl;

    @BeforeEach
    void setUp() throws IOException {
        server = HttpServer.create(new InetSocketAddress(0), 0);
        baseUrl = "http://localhost:" + server.getAddress().getPort();
        server.start();
    }

    @AfterEach
    void tearDown() {
        if (server != null) {
            server.stop(0);
        }
    }

    @Test
    void getComparisons_callsMlEndpoint() {
        server.createContext("/ml/models/comparisons", exchange -> {
            byte[] body = "{\"comparisons\":[]}".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        MlModelClient client = new MlModelClient(baseUrl);
        MlModelClient.ProxyResponse response = client.getComparisons();

        assertEquals(HttpStatus.OK, response.status());
        assertEquals("{\"comparisons\":[]}", response.body());
    }

    @Test
    void activateModel_callsMlEndpoint() {
        server.createContext("/ml/models/baseline/activate", exchange -> {
            byte[] body = "{\"modelId\":\"baseline\"}".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        MlModelClient client = new MlModelClient(baseUrl);
        MlModelClient.ProxyResponse response = client.activateModel("baseline");

        assertEquals(HttpStatus.OK, response.status());
        assertEquals("{\"modelId\":\"baseline\"}", response.body());
    }

    @Test
    void getActiveModel_callsMlEndpoint() {
        server.createContext("/ml/models/active", exchange -> {
            byte[] body = "{\"activeModel\":null}".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        MlModelClient client = new MlModelClient(baseUrl);
        MlModelClient.ProxyResponse response = client.getActiveModel();

        assertEquals(HttpStatus.OK, response.status());
        assertEquals("{\"activeModel\":null}", response.body());
    }
}
