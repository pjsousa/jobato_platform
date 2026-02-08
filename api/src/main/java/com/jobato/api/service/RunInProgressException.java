package com.jobato.api.service;

public class RunInProgressException extends RuntimeException {
    public RunInProgressException(String message) {
        super(message);
    }
}
