package com.jobato.api.service;

public class AllowlistNotFoundException extends RuntimeException {
    public AllowlistNotFoundException(String message) {
        super(message);
    }
}
