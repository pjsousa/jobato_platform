package com.jobato.api.service;

public class FeedbackNotFoundException extends RuntimeException {
    public FeedbackNotFoundException(String message) {
        super(message);
    }
}
