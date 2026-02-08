package com.jobato.api.service;

public class RunNotFoundException extends RuntimeException {
    public RunNotFoundException(String message) {
        super(message);
    }
}
