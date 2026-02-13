package com.jobato.api.controller;

import com.jobato.api.service.MlModelClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class MlModelControllerTest {

    private MlModelClient mlModelClient;
    private MlModelController controller;

    @BeforeEach
    void setUp() {
        mlModelClient = mock(MlModelClient.class);
        controller = new MlModelController(mlModelClient);
    }

    @Test
    void getComparisons_proxiesPayload() {
        when(mlModelClient.getComparisons()).thenReturn(new MlModelClient.ProxyResponse(HttpStatus.OK, "{\"comparisons\":[]}"));

        ResponseEntity<String> response = controller.getComparisons();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("{\"comparisons\":[]}", response.getBody());
        verify(mlModelClient).getComparisons();
    }

    @Test
    void activateModel_proxiesPayload() {
        when(mlModelClient.activateModel("baseline")).thenReturn(new MlModelClient.ProxyResponse(HttpStatus.OK, "{\"modelId\":\"baseline\"}"));

        ResponseEntity<String> response = controller.activateModel("baseline");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("{\"modelId\":\"baseline\"}", response.getBody());
        verify(mlModelClient).activateModel("baseline");
    }

    @Test
    void getActiveModel_proxiesPayload() {
        when(mlModelClient.getActiveModel()).thenReturn(new MlModelClient.ProxyResponse(HttpStatus.OK, "{\"activeModel\":null}"));

        ResponseEntity<String> response = controller.getActiveModel();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals("{\"activeModel\":null}", response.getBody());
        verify(mlModelClient).getActiveModel();
    }
}
