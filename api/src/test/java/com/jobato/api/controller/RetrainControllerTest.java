package com.jobato.api.controller;

import com.jobato.api.service.MlRetrainClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class RetrainControllerTest {

    private MlRetrainClient mlRetrainClient;
    private RetrainController controller;

    @BeforeEach
    void setUp() {
        mlRetrainClient = mock(MlRetrainClient.class);
        controller = new RetrainController(mlRetrainClient);
    }

    @Test
    void triggerRetrain_proxiesPayload() {
        when(mlRetrainClient.triggerRetrain()).thenReturn(new MlRetrainClient.ProxyResponse(HttpStatus.ACCEPTED, "{\"job\":{}}"));

        ResponseEntity<String> response = controller.triggerRetrain();

        assertEquals(HttpStatus.ACCEPTED, response.getStatusCode());
        assertEquals("{\"job\":{}}", response.getBody());
        verify(mlRetrainClient).triggerRetrain();
    }

    @Test
    void getStatus_proxiesPayload() {
        when(mlRetrainClient.getRetrainStatus()).thenReturn(new MlRetrainClient.ProxyResponse(HttpStatus.OK, "{\"latest\":null}"));

        ResponseEntity<String> response = controller.getStatus();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("{\"latest\":null}", response.getBody());
        verify(mlRetrainClient).getRetrainStatus();
    }

    @Test
    void getHistory_proxiesPayload() {
        when(mlRetrainClient.getRetrainHistory()).thenReturn(new MlRetrainClient.ProxyResponse(HttpStatus.OK, "{\"jobs\":[]}"));

        ResponseEntity<String> response = controller.getHistory();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("{\"jobs\":[]}", response.getBody());
        verify(mlRetrainClient).getRetrainHistory();
    }
}
